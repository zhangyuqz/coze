# 极光思维导图：扣子开发者使用说明

将 Markdown 标题和列表转换为思维导图，支持多语种混排、17 种字体模式、深浅主题，以及 PNG、WebP 和动态 GIF。图片在扣子云端生成，上传到扣子文件存储后返回图片地址和文件 ID，无需开发者另建绘图服务器或图床。

绘图运行包版本：`0.0.23-coze.1`。这不是 Dify 安装包，不能把 `.difypkg` 上传到扣子。

## 先了解接入方式

使用工具 `generate_mind_map`。当前扣子工作流中的自建插件参数没有可用的原生选项下拉框，字体、主题、格式请填写下表中的英文值，不能填写中文显示名。这里的字体模式影响对应字符的显示风格，不是语言翻译开关；混合文字会自动使用相应字体或回退字体。

本版不是零配置插件：第一次接入需要准备开发者自己的扣子 API 令牌和一个已发布的图片链接解析工作流。不要复制作者的令牌或工作流 ID。后续可复制自己已配置好的插件节点，仅更换 Markdown 和显示参数。

## 一、只需配置一次的内容

### 1. 创建图片链接解析工作流

1. 在自己的扣子空间中新建工作流，可命名为 `ribbon_file_url`。
2. “开始”节点新增必填参数 `image`，类型选 **Image（图片文件）**，不要选 String。
3. 将“开始”直接连接到“结束”。
4. “结束”选择“返回变量”，变量名填 `image_url`，变量值引用“开始 → image”。
5. 测试后发布该工作流。复制其网页地址中 `workflow_id=` 后的数字，作为插件的 `resolver_workflow_id`。不要复制整条网址，也不要把本插件所在工作流的 ID 填进去。

### 2. 准备扣子 API 令牌

使用开发者自己的扣子访问令牌，授权范围应包含文件上传和上述工作流的执行权限，填入 `coze_api_token`。令牌由插件传给扣子官方 API，不会发往字体或运行包下载地址。不要将真实令牌写进公开说明、GitHub 仓库或用户可见的回复。

### 3. 配置运行包地址

将下面整行填入 `runtime_bundle_url`。它包含公开绘图程序和字体，不包含用户正文或账号令牌。此地址在扣子云端完成过真实 PNG、WebP、GIF 生成验证；签名地址不是永久地址，失效后需要更新。

```text
https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e67e8e1e0da547c2b234b425305433cb.zip~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1884684948&x-signature=0f08%2BQpbaLa4Q6x0NG0oyPcf9W8%3D&x-wf-file_name=ribbon-coze-runtime-0.0.23-coze.1.zip
```

运行包来自 [GitHub Release](https://github.com/zhangyuqz/coze/releases/tag/coze-0.0.23-ide.1)，大小为 30,735,044 字节，SHA-256 为 `bb4fb401ecf8c95d55dd7c0c774399a27d577a5623e1ce70f9adf6dc68a820de`。程序会核对完整文件后使用。GitHub/CDN 下载路径在扣子中曾出现冷启动超时，因此不作为这里的首选配置。

## 二、插件节点参数怎么填

当前发布节点将这 10 个字段列为必填，请全部填写。代码里的回退值不能代替节点表单的必填要求。

| 参数 | 扣子类型 | 建议填写 | 用途 |
| --- | --- | --- | --- |
| `markdown_content` | String | 引用上游输出，或粘贴 Markdown | 要绘制的标题和列表 |
| `filename` | String | `mind-map` | 返回文件名；扩展名由输出格式确定 |
| `font_mode` | String | `heiti` | 字体模式，完整选项见下一节 |
| `theme` | String | `dark` | `dark` 深色；`light` 浅色 |
| `output_format` | String | `png` | `png` 静态 PNG；`webp` 静态 WebP；`gif` 动态 GIF |
| `render_scale` | Number | `0.56`；希望更清楚可用 `1.0` | 有效范围 0.42–1.0，超出时按边界处理；越大通常像素越多、耗时和内存也越多 |
| `max_blob_mb` | Number | `3.2`；大图可用 `4.5` | 内部压缩预算，范围 0.8–4.5 MiB；不是要求每张图都达到该大小，也不是扣子平台的文件大小上限 |
| `coze_api_token` | String | 自己的有效令牌 | 用于扣子文件上传和工作流执行 |
| `resolver_workflow_id` | String | 自己已发布的解析工作流 ID | 将上传后的文件 ID 转成图片链接 |
| `runtime_bundle_url` | String | 上一节完整地址 | 下载匹配本版的绘图程序和字体 |

**数字字段不要加引号。** 例如 JSON 中写 `"render_scale": 0.56`，不是 `"render_scale": "0.56"`。在节点里直接填数字即可。

`render_scale` 与 `max_blob_mb` 共同影响结果：清晰度调高，但文件预算过低时，程序仍可能压缩或缩小图片。建议先用 PNG、`render_scale=1.0`、`max_blob_mb=4.5` 检查较大的导图。文件小不一定模糊，应看实际像素和文字。WebP 存在 16,383 像素的单边限制，超长图会等比缩小；长图优先 PNG。GIF 还需要为多帧控制体积和内存，不能保证与静态 PNG 同尺寸。

## 三、字体选项：复制左列的值

| `font_mode` | 字体 | 主要用途 |
| --- | --- | --- |
| `heiti` | 思源黑体 | 默认中文；日文、韩文及混合内容可从此模式开始 |
| `chinese` | 朱雀仿宋 | 中文仿宋风格 |
| `fusion_pixel` | 缝合像素字体 | 中文像素风格 |
| `tiejili` | 铁蒺藜体 | 中文展示字体 |
| `zhi_mang_xing` | 钟齐志莽行书 | 中文行书风格 |
| `zcool_kuaile` | 站酷快乐体 | 中文活泼手写风格 |
| `english` | FreeSerif | 拉丁字母、西里尔字母及多语种回退 |
| `yeseva_one` | Yeseva One | 拉丁字母、西里尔字母展示风格 |
| `bad_script` | Bad Script | 拉丁字母、西里尔字母手写风格 |
| `uyghur` | Noto Naskh Arabic | 维吾尔语、阿拉伯字母文字 |
| `tibetan` | Noto Serif Tibetan | 藏文 |
| `mongolian` | Noto Sans Mongolian | 传统蒙古文；西里尔蒙古语可使用前述西里尔字体模式 |
| `lao` | Noto Sans Lao | 老挝文 |
| `myanmar` | Noto Sans Myanmar | 缅甸文 |
| `khmer` | Noto Sans Khmer | 高棉文 |
| `telugu` | Noto Sans Telugu | 泰卢固文 |
| `kannada` | Noto Sans Kannada | 卡纳达文 |

没有单独的日文、韩文字体参数值。选用一种中文或西文字体，不代表其他文字也会强制使用该字体；未覆盖字符会回退，特定文字会自动路由到专用字体。传统蒙古文支持不等于全文纵向排版。具体字形覆盖受内置字体影响，不承诺覆盖所有 Unicode 字符。

## 四、第一次运行：可复制示例

工作流采用“开始 → generate_mind_map → 结束”。将以下正文填入 `markdown_content`，其他参数先用上表建议值。

```markdown
# 世界地图 World שלום مرحبا

## 自然 Nature ธรรมชาติ
### 山と川 नदी
### 숲과 호수

## 都市 Πόλη мир
### Старый город
### ខ្មែរ 港口
```

在普通文本框里请保留真实换行，不要把换行全部写成两个字符 `\n`。如果使用 JSON 测试输入，JSON 字符串中的 `\n` 则会被正常解析为换行。

下面是完整 JSON 结构。令牌和工作流 ID 是占位符，替换为自己的配置后才能运行。

```json
{
  "markdown_content": "# 世界地图 World שלום مرحبا\n\n## 自然 Nature\n### 山と川 नदी\n### 숲과 호수\n\n## 都市\n### Старый город\n### 港口",
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

## 五、如何判断成功，以及向用户显示什么

先判断 `success` 是否为 `true`。只有为真时才显示 `image_markdown` 或使用 `image_url`。为假时显示 `error_stage` 和 `error`。扣子页面显示“测试通过”只代表函数返回了结果，并不保证图片生成成功。

| 返回字段 | 用途 |
| --- | --- |
| `success` | Boolean，图片生成与返回链路是否成功 |
| `image_markdown` | 可直接用于支持 Markdown 的回复或页面组件显示图片 |
| `image_url` / `download_url` | 同一条扣子签名图片链接，可预览或下载；不是永久链接 |
| `file_id` | 扣子文件 ID，不是网址，不能直接放入图片地址栏 |
| `filename` / `mime_type` | 文件名与实际格式 |
| `width` / `height` | 图片真实像素宽高 |
| `size_bytes` | 实际文件字节数 |
| `error_stage` / `error` | 失败阶段和具体原因 |

推荐增加判断节点：成功分支返回 `image_markdown`；失败分支返回 `error_stage` 与 `error`。不要只返回图片字段，否则失败时用户会看到空白。

## 六、常见问题

| 失败阶段或现象 | 优先检查 |
| --- | --- |
| `runtime` | 运行包地址是否可达、是否过期、是否匹配本版；首次下载通常比缓存命中慢 |
| `dependencies` | 自建 IDE 副本是否安装了 Pillow、matplotlib、numpy、uharfbuzz、freetype-py、python-bidi；使用商店插件者不用自行安装这些包 |
| `render` | Markdown 是否为空、真实换行是否保留，并读取具体错误；大图先用 PNG |
| `upload` | 令牌是否有效，是否拥有文件上传权限 |
| `resolve` | 解析工作流是否已发布、ID 是否正确、令牌是否有执行权限、输入是否为 Image、输出是否叫 image_url |
| 成功但回复空白 | 下游是否引用 image_markdown/image_url，而不是 file_id |
| 放大仍模糊 | 检查实际 width/height；适当提高 render_scale 和 max_blob_mb；超长图改用 PNG |

图片在扣子生成并托管；本插件不调用大模型生成图片。冷启动需要联网下载公开程序和字体。并发量、运行时限、存储和费用受扣子账号规则约束，不承诺无限免费或任意规模并发。

正文不会发送到运行包下载服务。图片会上传到扣子；平台可能保存工作流输入、运行记录和文件，令牌作为输入也可能出现在开发者可见的运行记录中。不要将含令牌的配置公开分享。

## 参考

- [扣子文件上传 API](https://docs.coze.cn/developer_guides_upload_files)
- [扣子工作流执行 API](https://docs.coze.cn/developer_guides_workflow_run)
- [插件市场发布说明](https://docs.coze.cn/guides_publish_plugin_to_store)
- [项目仓库](https://github.com/zhangyuqz/coze)
