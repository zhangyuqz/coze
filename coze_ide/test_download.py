"""Targeted local tests for the download recovery change, not cloud acceptance."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import urllib.error


class DownloadTests(unittest.TestCase):
    """Check only transfer recovery, exact-byte verification and retry boundaries."""

    def setUp(self):
        """Load the delivered handler with Coze type declarations stubbed locally."""
        runtime = types.ModuleType("runtime")
        runtime.Args = object
        declarations = types.ModuleType("typings.generate_mind_map.generate_mind_map")
        declarations.Input = declarations.Output = dict
        sys.modules["runtime"] = runtime
        sys.modules[declarations.__name__] = declarations
        spec = importlib.util.spec_from_file_location("candidate", Path(__file__).with_name("handler.py"))
        self.handler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.handler)
        self.body = b"PK-test-runtime-bytes"
        self.handler.RUNTIME_SHA256 = hashlib.sha256(self.body).hexdigest()
        self.logger = types.SimpleNamespace(info=lambda message: None)
        self.temporary = tempfile.TemporaryDirectory(prefix="coze_download_test_")
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "runtime.zip"
        self.url = "https://github.com/zhangyuqz/coze/releases/download/coze-0.0.23-ide.1/ribbon-coze-runtime-0.0.23-coze.1.zip"

    def test_success_preserves_bytes_and_octet_stream(self):
        """The normal path must keep every byte and request binary content."""
        with patch.object(self.handler.urllib.request, "urlopen", return_value=io.BytesIO(self.body)) as request:
            self.handler._download_runtime(self.url, self.target, self.logger)
        self.assertEqual(self.target.read_bytes(), self.body)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.args[0].get_header("Accept"), "application/octet-stream")

    def test_timeout_uses_official_asset_route(self):
        """A transient failure on the published URL must try the same official asset."""
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=[urllib.error.URLError("timed out"), io.BytesIO(self.body)]) as request:
            self.handler._download_runtime(self.url, self.target, self.logger)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args[0].full_url, "https://api.github.com/repos/zhangyuqz/coze/releases/assets/580946709")
        self.assertEqual(self.target.read_bytes(), self.body)

    def test_custom_source_is_not_replaced(self):
        """A supplied alternate source is retried as supplied, without silently swapping it."""
        source = "https://example.test/runtime.zip"
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=[TimeoutError(), io.BytesIO(self.body)]) as request:
            self.handler._download_runtime(source, self.target, self.logger)
        self.assertEqual([call.args[0].full_url for call in request.call_args_list], [source, source])

    def test_bad_hash_is_not_retried_or_extracted(self):
        """A wrong runtime remains an explicit failure, not an accepted fallback artifact."""
        with patch.object(self.handler.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong archive")) as request:
            with self.assertRaisesRegex(RuntimeError, "not the ZIP"):
                self.handler._download_runtime(self.url, self.target, self.logger)
        self.assertEqual(request.call_count, 1)

    def test_retry_exhaustion_propagates(self):
        """Two failed routes must return the actual error without an unbounded loop."""
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=urllib.error.URLError("timed out")) as request:
            with self.assertRaises(urllib.error.URLError):
                self.handler._download_runtime(self.url, self.target, self.logger)
        self.assertEqual(request.call_count, 2)

    def test_nontransient_http_error_is_not_retried(self):
        """An absent artifact is reported directly instead of masking it with retries."""
        error = urllib.error.HTTPError(self.url, 404, "not found", {}, None)
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaises(urllib.error.HTTPError):
                self.handler._download_runtime(self.url, self.target, self.logger)
        self.assertEqual(request.call_count, 1)

    def test_manifest_reconstructs_exact_original(self):
        """Parallel piece downloads must reconstruct the exact original ZIP byte order."""
        pieces = [self.body[:7], self.body[7:]]
        manifest = {
            "format": "ribbon-runtime-parts-v1", "sha256": self.handler.RUNTIME_SHA256,
            "size_bytes": len(self.body),
            "parts": [{"file": f"part-{index}", "size_bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest()}
                      for index, data in enumerate(pieces)],
        }
        def respond(request, **kwargs):
            if request.full_url.endswith("manifest.json"):
                return io.BytesIO(json.dumps(manifest).encode())
            return io.BytesIO(pieces[int(request.full_url.rsplit("-", 1)[1])])
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=respond):
            self.handler._download_runtime("https://example.test/manifest.json", self.target, self.logger)
        self.assertEqual(self.target.read_bytes(), self.body)

    def test_manifest_rejects_wrong_piece(self):
        """A damaged piece must not reach extraction or produce an accepted archive."""
        manifest = {
            "format": "ribbon-runtime-parts-v1", "sha256": self.handler.RUNTIME_SHA256,
            "size_bytes": len(self.body),
            "parts": [{"file": "part-0", "size_bytes": len(self.body),
                       "sha256": self.handler.RUNTIME_SHA256}],
        }
        def respond(request, **kwargs):
            return io.BytesIO(json.dumps(manifest).encode() if request.full_url.endswith("manifest.json") else b"damaged")
        with patch.object(self.handler.urllib.request, "urlopen", side_effect=respond):
            with self.assertRaisesRegex(RuntimeError, "failed byte verification"):
                self.handler._download_runtime("https://example.test/manifest.json", self.target, self.logger)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
