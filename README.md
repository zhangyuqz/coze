# Ribbon Mind Map for Coze

Convert Markdown headings and lists into multilingual mind maps. The Coze cloud tool supports 17 font modes, dark/light themes, PNG, static WebP and animated GIF. It renders in Coze, uploads the result to Coze file storage and returns a file ID and signed image URL. No separately hosted rendering server is needed.

[Chinese developer guide](readme/README_zh_Hans.md)

Drawing runtime: `0.0.23-coze.1`, based on Dify `0.0.23`. A Dify `.difypkg` is not a Coze installation package. The Coze entry-point tool is `generate_mind_map`.

## One-time setup

This version requires the developer's own Coze API token and a published file-resolution workflow. Do not copy the author's credentials or workflow ID.

1. Create a workflow in your own Coze space. Its Start node must have a required **Image** file input named `image`, not a String input.
2. Connect Start directly to End. Choose variable output, name it `image_url`, and bind its value to Start > image.
3. Test and publish that workflow. Copy the numeric `workflow_id` from its browser URL into `resolver_workflow_id`.
4. Supply your own Coze access token with file-upload and workflow-execution permissions as `coze_api_token`. Configure access to your resolver workflow.
5. Set `runtime_bundle_url` to the complete value below. It contains only public program and font files. It was used in real Coze cloud PNG/WebP/GIF tests, but it is a signed URL, not permanent hosting.

```text
https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e67e8e1e0da547c2b234b425305433cb.zip~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1884684948&x-signature=0f08%2BQpbaLa4Q6x0NG0oyPcf9W8%3D&x-wf-file_name=ribbon-coze-runtime-0.0.23-coze.1.zip
```

The runtime is the unchanged [release bundle](https://github.com/zhangyuqz/coze/releases/tag/coze-0.0.23-ide.1): 30,735,044 bytes, SHA-256 `bb4fb401ecf8c95d55dd7c0c774399a27d577a5623e1ce70f9adf6dc68a820de`. The tool verifies the complete file before use. GitHub/CDN routes have timed out on Coze cold workers, so they are not the preferred configuration here.

## Input parameters

The currently published Coze node marks all ten fields as required. Fill all of them; code-level fallback values do not bypass the node editor's required-field checks. Custom plugin-node parameters did not display native enum dropdowns in actual Coze.cn testing. Enter the literal values below, or bind values from your own workflow.

| Parameter | Type | Suggested value | Meaning |
| --- | --- | --- | --- |
| `markdown_content` | String | Markdown from an upstream node | Headings and lists to draw; preserve actual newlines |
| `filename` | String | `mind-map` | Output display name; the format determines its extension |
| `font_mode` | String | `heiti` | Font mode from the table below |
| `theme` | String | `dark` | `dark` or `light` |
| `output_format` | String | `png` | `png`, `webp`, or animated `gif` |
| `render_scale` | Number | `0.56`; use `1.0` for more pixels | Effective range 0.42-1.0; values outside it are clamped |
| `max_blob_mb` | Number | `3.2`; up to `4.5` for large maps | Internal encoding budget in MiB, clamped to 0.8-4.5; not a target file size or a Coze platform upload limit |
| `coze_api_token` | String | Your own token | Used only with official Coze file/workflow APIs |
| `resolver_workflow_id` | String | Your published resolver's ID | Converts the uploaded file ID into an image URL |
| `runtime_bundle_url` | String | Complete URL above | Downloads the program and fonts paired with this release |

Use JSON numbers, not strings: `"render_scale": 0.56`, not `"render_scale": "0.56"`. A higher scale can still be reduced by a small encoding budget. For a large map, first try PNG with scale `1.0` and budget `4.5`. Inspect actual pixel dimensions rather than judging clarity by file size. WebP has a 16,383-pixel edge limit, so very long images are downscaled; prefer PNG for those maps. GIF has additional frame-related size and memory constraints.

## Font values

These modes select appearance, not translation. Script-specific routing and missing-glyph fallback remain active. No individual font is claimed to cover every supported script.

| Value | Font | Primary use |
| --- | --- | --- |
| `heiti` | Source Han Sans | Default Chinese; starting point for Japanese/Korean and mixed text |
| `chinese` | Zhuque Fangsong | Chinese Fangsong style |
| `fusion_pixel` | Fusion Pixel | Chinese pixel style |
| `tiejili` | Tiejili | Chinese display style |
| `zhi_mang_xing` | Zhi Mang Xing | Chinese running-script style |
| `zcool_kuaile` | ZCOOL KuaiLe | Playful Chinese handwriting |
| `english` | FreeSerif | Latin/Cyrillic and multilingual fallback |
| `yeseva_one` | Yeseva One | Latin/Cyrillic display style |
| `bad_script` | Bad Script | Latin/Cyrillic handwriting |
| `uyghur` | Noto Naskh Arabic | Uyghur and Arabic-script text |
| `tibetan` | Noto Serif Tibetan | Tibetan |
| `mongolian` | Noto Sans Mongolian | Traditional Mongolian; not full vertical page layout |
| `lao` | Noto Sans Lao | Lao |
| `myanmar` | Noto Sans Myanmar | Myanmar |
| `khmer` | Noto Sans Khmer | Khmer |
| `telugu` | Noto Sans Telugu | Telugu |
| `kannada` | Noto Sans Kannada | Kannada |

There are no separate Japanese or Korean mode values. Cyrillic Mongolian can use a Cyrillic font mode. Character coverage depends on the bundled fonts, with script routing and fallback where applicable.

## Copy-ready request structure

Replace the two credential/workflow placeholders with your own configuration before running. Never publish real tokens. In a JSON string, `\n` represents a newline; in a normal Markdown text field, paste actual line breaks.

```json
{
  "markdown_content": "# World map\n\n## Nature\n### Mountains\n### Lakes\n\n## Cities\n### Old town\n### Harbour",
  "filename": "mind-map",
  "font_mode": "heiti",
  "theme": "dark",
  "output_format": "png",
  "render_scale": 0.56,
  "max_blob_mb": 3.2,
  "coze_api_token": "YOUR_COZE_API_TOKEN",
  "resolver_workflow_id": "YOUR_PUBLISHED_RESOLVER_WORKFLOW_ID",
  "runtime_bundle_url": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e67e8e1e0da547c2b234b425305433cb.zip~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1884684948&x-signature=0f08%2BQpbaLa4Q6x0NG0oyPcf9W8%3D&x-wf-file_name=ribbon-coze-runtime-0.0.23-coze.1.zip"
}
```

## Outputs and workflow wiring

Use Start -> `generate_mind_map` -> a condition on `success`. On success, display `image_markdown` in a Markdown-capable response/component, or use `image_url`. On failure, return `error_stage` and `error`; returning only the image field would hide the failure behind a blank response.

| Output | Meaning |
| --- | --- |
| `success` | Boolean indicating that rendering, upload and URL resolution succeeded |
| `image_markdown` | Ready-to-display Markdown image |
| `image_url`, `download_url` | The same signed Coze image URL; not a permanent link |
| `file_id` | Coze file identifier, not an image URL |
| `filename`, `mime_type` | Display name and actual image MIME type |
| `width`, `height`, `size_bytes` | Actual pixel dimensions and encoded byte count |
| `error_stage`, `error` | Failure stage and specific error |

A green IDE test badge only means the handler returned a response. Always check `success` and the actual image.

## Troubleshooting and limits

- `runtime`: check reachability, expiry and version of the bundle URL. Cold starts download public code/fonts and are slower than cache hits.
- `dependencies`: developers installing an IDE copy need Pillow, matplotlib, numpy, uharfbuzz, freetype-py and python-bidi. Marketplace users do not install these packages themselves.
- `render`: check empty Markdown, real newlines and the detailed error. Prefer PNG for long maps.
- `upload`: check the token and file-upload permission.
- `resolve`: check the published resolver ID, its execution permission, its Image input `image` and output `image_url`.
- Blank response after success: bind the image URL or Markdown, not `file_id`.

No LLM or external image-generation service is used for rendering. Coze quotas, execution time limits, storage and fees still depend on the account; this is not a promise of unlimited free execution or arbitrary concurrency. Ten-way large-map concurrency is not certified by these Coze tests.

Private Markdown and credentials are not sent to the runtime download host. Generated images are uploaded to Coze. Coze may retain workflow inputs, execution records and files; tokens supplied as inputs may be visible in developer execution records. Do not share configured workflows or screenshots containing credentials publicly. The renderer uses temporary request files and caches public runtime assets separately.

## References

- [Coze file upload](https://docs.coze.cn/developer_guides_upload_files)
- [Coze workflow execution](https://docs.coze.cn/developer_guides_workflow_run)
- [Coze plugin marketplace publication](https://docs.coze.cn/guides_publish_plugin_to_store)
