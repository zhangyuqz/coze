"""Coze low-code IDE tool: render in its sandbox, then upload to Coze file storage."""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import urllib.parse
from uuid import uuid4
import zipfile

from runtime import Args
from typings.generate_mind_map.generate_mind_map import Input, Output


# Filled by the local build from the exact runtime ZIP, never from user input.
RUNTIME_SHA256 = "bb4fb401ecf8c95d55dd7c0c774399a27d577a5623e1ce70f9adf6dc68a820de"
_BOOT_LOCK = threading.Lock()
_API_ROOT = "https://api.coze.cn"


def _value(inputs, name, default=None):
    """Read Coze's typed Input and the dictionary form used by local contract tests."""
    if isinstance(inputs, dict):
        return inputs.get(name, default)
    return getattr(inputs, name, default)


def _download_runtime_parts(bundle_url, archive_path, logger):
    """Fetch immutable runtime pieces concurrently, then verify the unchanged full ZIP."""
    deadline = time.monotonic() + 90
    request = urllib.request.Request(bundle_url, headers={"User-Agent": "ribbon-coze/0.0.23"})
    with urllib.request.urlopen(request, timeout=12) as response:
        manifest = json.load(response)
    if manifest["sha256"] != RUNTIME_SHA256 or manifest["format"] != "ribbon-runtime-parts-v1":
        raise RuntimeError("The runtime manifest does not identify this handler's release.")
    parts = manifest["parts"]
    logger.info(f"ribbon_coze: runtime parts={len(parts)}; parallel download starting")

    def receive_part(item):
        """Download one program-owned piece; no user Markdown or credentials are transmitted."""
        index, part = item
        path = archive_path.parent / f"runtime-part-{index:02d}"
        url = urllib.parse.urljoin(bundle_url, part["file"])
        for attempt in range(2):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Runtime part download exceeded its 90-second budget.")
            try:
                digest = hashlib.sha256()
                received = 0
                request = urllib.request.Request(url, headers={"User-Agent": "ribbon-coze/0.0.23"})
                with urllib.request.urlopen(request, timeout=min(12, remaining)) as response, path.open("wb") as target:
                    while True:
                        block = response.read1(65536)
                        if not block:
                            break
                        target.write(block)
                        digest.update(block)
                        received += len(block)
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Runtime part download exceeded its 90-second budget.")
                if received != part["size_bytes"] or digest.hexdigest() != part["sha256"]:
                    raise RuntimeError(f"Runtime part {index + 1} failed byte verification.")
                return index, path
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                if isinstance(error, urllib.error.HTTPError) and error.code not in (408, 429, 500, 502, 503, 504):
                    raise
                if attempt == 1 or time.monotonic() >= deadline:
                    raise

    completed = {}
    # Only lightweight network transfers run together; image rendering stays serialized.
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(parts))) as executor:
        futures = [executor.submit(receive_part, item) for item in enumerate(parts)]
        for future in concurrent.futures.as_completed(futures):
            index, path = future.result()
            completed[index] = path
            logger.info(f"ribbon_coze: runtime parts completed={len(completed)}/{len(parts)}")
    digest = hashlib.sha256()
    written = 0
    with archive_path.open("wb") as target:
        for index in range(len(parts)):
            with completed[index].open("rb") as source:
                for block in iter(lambda: source.read(65536), b""):
                    target.write(block)
                    digest.update(block)
                    written += len(block)
    if written != manifest["size_bytes"] or digest.hexdigest() != RUNTIME_SHA256:
        raise RuntimeError("The reconstructed runtime is not the ZIP paired with this handler.")
    logger.info(f"ribbon_coze: runtime verified; bytes={written}")


def _download_runtime(bundle_url, archive_path, logger):
    """Download this exact release, retrying transient transport failures once."""
    if urllib.parse.urlsplit(bundle_url).path.endswith(".json"):
        return _download_runtime_parts(bundle_url, archive_path, logger)
    primary_url = "https://github.com/zhangyuqz/coze/releases/download/coze-0.0.23-ide.1/ribbon-coze-runtime-0.0.23-coze.1.zip"
    asset_url = "https://api.github.com/repos/zhangyuqz/coze/releases/assets/580946709"
    # Both official URLs identify the already-published, hash-pinned runtime.
    routes = [bundle_url, asset_url if bundle_url == primary_url else bundle_url]
    for attempt, url in enumerate(routes, 1):
        started = time.monotonic()
        received = 0
        next_progress = 8 * 1024 * 1024
        digest = hashlib.sha256()
        logger.info(f"ribbon_coze: runtime download attempt={attempt}; connecting")
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "ribbon-coze/0.0.23", "Accept": "application/octet-stream"},
            )
            with urllib.request.urlopen(request, timeout=12) as response, archive_path.open("wb") as target:
                logger.info(f"ribbon_coze: runtime download attempt={attempt}; connected")
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                    if received >= next_progress:
                        logger.info(f"ribbon_coze: runtime download bytes={received}")
                        next_progress += 8 * 1024 * 1024
                    if time.monotonic() - started > 60:
                        raise TimeoutError("Runtime transfer exceeded the 60-second progress deadline.")
            if digest.hexdigest() != RUNTIME_SHA256:
                raise RuntimeError("Runtime download is not the ZIP paired with this handler.")
            logger.info(f"ribbon_coze: runtime downloaded; bytes={received}; seconds={time.monotonic()-started:.2f}")
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code not in (408, 429, 500, 502, 503, 504):
                raise
            logger.info(f"ribbon_coze: runtime download attempt={attempt} failed; bytes={received}; {type(error).__name__}")
            if attempt == len(routes):
                raise


def _runtime(bundle_url, logger):
    """Install the verified runtime and report download, extraction and import stages."""
    cache = Path(tempfile.gettempdir()) / ("ribbon_coze_" + RUNTIME_SHA256[:16])
    with _BOOT_LOCK:
        cache.mkdir(parents=True, exist_ok=True)
        lock_handle = (cache / "bootstrap.lock").open("a+b")
        try:
            # Separate IDE workers may share /tmp: publish a complete cache atomically.
            if os.name == "posix":
                import fcntl
                fcntl.flock(lock_handle, fcntl.LOCK_EX)
            ready = cache / "runtime"
            if not (ready / "render_image.py").is_file():
                with tempfile.TemporaryDirectory(prefix="install_", dir=cache) as work:
                    archive_path = Path(work) / "runtime.zip"
                    _download_runtime(bundle_url, archive_path, logger)
                    logger.info("ribbon_coze: runtime extracting")
                    unpacked = Path(work) / "unpacked"
                    with zipfile.ZipFile(archive_path) as archive:
                        archive.extractall(unpacked)
                    unpacked.rename(ready)
            else:
                logger.info("ribbon_coze: runtime cache hit")
            if str(ready) not in sys.path:
                sys.path.insert(0, str(ready))
            logger.info("ribbon_coze: runtime importing")
            return importlib.import_module("render_image")
        finally:
            lock_handle.close()



def _api(request, token):
    """Execute one documented Coze API call; preserve errors without logging credentials."""
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if token:
            detail = detail.replace(token, "[REDACTED]")
        raise RuntimeError(f"Coze HTTP {error.code}: {detail[:600]}") from None
    if payload.get("code", 0) != 0:
        message = str(payload.get("msg", "Coze API failed"))
        if token:
            message = message.replace(token, "[REDACTED]")
        raise RuntimeError(f"Coze API {payload['code']}: {message[:600]}")
    return payload


def _upload(artifact, token):
    """Send the actual encoded image to the official file-upload endpoint."""
    boundary = "ribbon_" + uuid4().hex
    suffix = Path(artifact["image_path"]).suffix
    # Use a generated multipart filename; the original display name remains in our output.
    wire_name = "mind-map-" + uuid4().hex + suffix
    prefix = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
              f"filename=\"{wire_name}\"\r\nContent-Type: {artifact['mime_type']}\r\n\r\n").encode("ascii")
    body = prefix + Path(artifact["image_path"]).read_bytes() + f"\r\n--{boundary}--\r\n".encode("ascii")
    request = urllib.request.Request(
        _API_ROOT + "/v1/files/upload", data=body, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "multipart/form-data; boundary=" + boundary},
    )
    return str(_api(request, token)["data"]["id"])


def _resolve(file_id, workflow_id, token):
    """Pass the uploaded ID to a published File-input workflow and read its URL output."""
    body = {"workflow_id": workflow_id,
            "parameters": {"image": json.dumps({"file_id": file_id})}}
    request = urllib.request.Request(
        _API_ROOT + "/v1/workflow/run", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    response = _api(request, token)
    data = response["data"]
    if isinstance(data, str):
        data = json.loads(data)
    # A returned ID is not a download URL. Surface a resolver failure instead of a false success.
    image_url = data.get("image_url") if isinstance(data, dict) else None
    if not isinstance(image_url, str) or not image_url.startswith(("https://", "http://")):
        raise RuntimeError("Resolver did not return image_url as a URL. Its image input must be File, not String.")
    return image_url


def handler(args: Args[Input]) -> Output:
    """Serve one IDE invocation and report the exact stage when output cannot be delivered."""
    started = time.monotonic()
    stage = "runtime"
    uploaded_id = ""
    token = str(_value(args.input, "coze_api_token", "") or "")
    try:
        args.logger.info("ribbon_coze: runtime; token received=" + str(bool(token)))
        engine = _runtime(_value(args.input, "runtime_bundle_url", ""), args.logger)
        stage = "dependencies"
        args.logger.info("ribbon_coze: dependencies checking")
        engine.check_runtime()
        args.logger.info("ribbon_coze: dependencies ready")
        parameters = {name: _value(args.input, name, default) for name, default in (
            ("markdown_content", ""), ("filename", "mind-map"), ("font_mode", "heiti"),
            ("theme", "dark"), ("output_format", "png"), ("render_scale", 0.56),
            ("max_blob_mb", 3.2),
        )}
        stage = "render"
        args.logger.info("ribbon_coze: render starting")
        # Final artifacts go to Coze storage; no private Markdown or image is kept in /tmp.
        with tempfile.TemporaryDirectory(prefix="ribbon_coze_result_") as output_dir:
            artifact = engine.render(parameters, output_dir)
            stage = "upload"
            args.logger.info("ribbon_coze: upload; bytes=" + str(artifact["size_bytes"]))
            uploaded_id = _upload(artifact, token)
            stage = "resolve"
            args.logger.info("ribbon_coze: resolving uploaded file")
            image_url = _resolve(uploaded_id, str(_value(args.input, "resolver_workflow_id", "")), token)
        args.logger.info("ribbon_coze: completed; seconds=" + str(round(time.monotonic() - started, 3)))
        return {
            "success": True, "image_url": image_url, "download_url": image_url,
            "image_markdown": "![Mind map](" + image_url + ")", "file_id": uploaded_id,
            "filename": artifact["filename"], "mime_type": artifact["mime_type"],
            "width": artifact["width"], "height": artifact["height"],
            "size_bytes": artifact["size_bytes"], "error_stage": "", "error": "",
        }
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        if token:
            message = message.replace(token, "[REDACTED]")
        args.logger.error("ribbon_coze failed at " + stage + ": " + message[:800])
        return {
            "success": False, "image_url": "", "download_url": "", "image_markdown": "",
            "file_id": uploaded_id, "filename": "", "mime_type": "", "width": 0,
            "height": 0, "size_bytes": 0, "error_stage": stage, "error": message[:800],
        }
