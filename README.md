# Ribbon Mind Map for Coze IDE

Coze network-bootstrap fix, tested in an authenticated Coze IDE account on September 22, 2026. The drawing runtime remains `0.0.23-coze.1`, based on Dify `0.0.23`.

[Chinese guide](readme/README_zh_Hans.md)

## Status

The original GitHub Release download timed out in the Coze sandbox before drawing began. The updated [handler](coze_ide/handler.py) downloads eight immutable runtime pieces through jsDelivr, checks every piece, and verifies the reconstructed ZIP before using it. The renderer, fonts, layout rules and original Dify package are unchanged.

Four real cloud tests completed generation, Coze file upload, URL resolution through the existing published helper workflow, and download of the resulting file:

| Input | Font | Theme / format | Actual pixels | Bytes |
| --- | --- | --- | --- | ---: |
| World-map multilingual smoke sample | `heiti` | Dark PNG | 1120 x 580 | 63,826 |
| Existing 30-language small sample | `yeseva_one` | Light WebP | 1910 x 7223 | 378,814 |
| Existing 30-language stress sample | `bad_script` | Dark PNG | 2826 x 19950 | 2,239,987 |
| World-map multilingual smoke sample | `zcool_kuaile` | Dark GIF, 12 frames | 1080 x 564 | 166,527 |

Actual downloaded artifacts were opened and visually inspected. Representative complex-script, mixed-shape, long-text and deep-chain regions were checked in a real browser at native image pixels. GIF border colors visibly changed between observations. No border/text collision, node overlap or broken connector was observed in the inspected regions. This is not a claim that every glyph, font and parameter combination has been exhaustively certified.

The plugin remains unpublished. Ordinary workflow invocation of a published plugin node, public marketplace publication, ten-way concurrency and every font/format combination were not tested in this cloud session. A green IDE test badge alone is not success: check `success`, `error_stage` and a usable output file.

## Current runtime URL

Use this entire value for `runtime_bundle_url`:

```text
https://cdn.jsdelivr.net/gh/zhangyuqz/coze@3911bdaa71ec797929e457bda8c24e7bc004f7ae/runtime/0.0.23-coze.1/manifest.json
```

The immutable runtime ZIP is 30,735,044 bytes, with SHA-256:

```text
bb4fb401ecf8c95d55dd7c0c774399a27d577a5623e1ce70f9adf6dc68a820de
```

Only public program/font assets are fetched from the CDN. Markdown, API credentials and generated images are not sent there. Images are generated in Coze and uploaded to Coze. No paid server, paid image host or paid plan was enabled. Coze account quotas and possible platform charges still depend on the account. Cold starts still need external network access; this change does not guarantee zero future network failures.

## IDE configuration

Use the existing Python IDE tool named `generate_mind_map`. Replace its code with `coze_ide/handler.py`. Add the six dependencies listed in `coze_ide/requirements.txt`. `coze_ide/metadata.json` is a manual field reference, not an importable workflow or plugin schema.

- `render_scale` and `max_blob_mb` must be **Number**, not String.
- `success` must be Boolean. `width`, `height` and `size_bytes` must be Number.
- Keep the existing Coze API credential in Coze, not this repository.
- `resolver_workflow_id` must identify the already-published workflow that converts the uploaded File input into `image_url`.
- Returned URLs are signed platform URLs, not permanent public hosting links.

The runtime pieces are distribution data, not separate plugins. Do not upload the repository ZIP into a Dify package or Coze workflow import dialog.

## References

- [Coze IDE](https://docs.coze.cn/guides_ide)
- [Coze file upload](https://docs.coze.cn/developer_guides_upload_files)
- [Coze workflow execution API](https://docs.coze.cn/developer_guides_workflow_run)
- [jsDelivr documentation](https://github.com/jsdelivr/jsdelivr)
