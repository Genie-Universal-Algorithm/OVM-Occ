# OVM-Occ 项目主页初版

内容依据：上一级目录的 `pages.md`。网页为英文静态 HTML / CSS / JavaScript，资源均在此目录中，无需安装前端依赖，也不依赖外部字体或 CDN。

## 打开网页

在终端运行：

```bash
cd '/Users/agiuser/Documents/OVm-Occ 资料/网页开发/site'
python3 preview.py
```

然后用浏览器打开 http://127.0.0.1:8000 。预览服务仅在本机提供访问，并支持视频进度拖动。结束时按 Control+C。如果端口占用，可使用 `python3 preview.py --port 8001`，并相应打开 8001 地址。

也可用 Chrome / Safari 直接打开本目录的 `index.html`。所有资源使用相对路径；浏览器剪贴板限制可能影响直接打开模式下的引用复制，此时可手动选择引用文本复制。

## 已包含

- 项目标题、完整作者与单位、教师–学生蒸馏概览图；四项贡献置于摘要之前。
- 教师和学生框架图；点击放大，Esc 或 Close 关闭。
- 9 个视频场景：性能对比 2 个、真实环境少样本适应 3 个、全局建图 3 个、语义导航 1 个。
- 当前展示内容以手动编辑后的 `index.html` 为准；用户已移除的 Results 表格区不自动恢复。
- Experiments 与 Application 分为同级栏目；所有 9 个场景直接上下展开，提供视频播放控制及 BibTeX 复制。
- 桌面和手机布局规则，宽表局部横向滚动，方法图完整等比例呈现。

论文和代码按钮按需求隐藏。引用文本使用文档提供的 BibTeX。当前仅为本地初版，未上传或发布。

## 内容与素材

- `index.html`：可直接打开的页面。
- `styles.css`、`app.js`：样式和交互。
- `assets/`：网站需要的全部图片、视频与图标。
- `tools/build_page.py`：将 `pages.md` 的摘要、贡献、方法图说明、4 张结果表和 BibTeX 写入网页。场景映射与部分页面文案在脚本中定义；修改场景清单时同步更新映射。
- `tools/prepare_media.py`：从原始素材生成网页视频和封面，需要 Pillow 与 FFmpeg；本机路径可自动发现，其他电脑可用 `FFMPEG` 环境变量指定。
- `tools/media-manifest.json`：视频来源、时长、尺寸和处理记录。

日常修改以当前 `index.html` 为准，只对指定位置做局部编辑，保留用户手动修改。`pages.md` 和生成脚本用于内容参考，不能用它们恢复用户已删除的网页内容。生成脚本默认拒绝覆盖已有网页；只有明确决定放弃当前页面中的手动改动并完整重建时，才使用 `--overwrite`。

视频为原素材的 H.264 网页副本，保持原始时间顺序、播放速度和语义配色；将已有透明通道合成到白底，不做插帧、不补造预测结果。对比视频使用 RGB / GT / LegoOcc / OVM-Occ 单行四列排版；三组 Occ 根据全部源帧采用统一固定裁边，减少透明留白并等比例放大，其余建图视频使用 RGB / 局部占据 / 全局地图的三列排版。原始文件保持不变。

## 核验范围

核对页面资源链接、4 张表与 `pages.md` 的全部单元格、锚点和标签对应、JavaScript 语法、视频完整解码，以及本地 HTTP / 视频 Range 请求。方法图和视频封面已做视觉检查。

当前会话的浏览器工具不可用，因此桌面 / 手机的实际浏览器排版、交互和播放效果尚未完成浏览器实测。参考站点在制作时也无法连接；本版按需求文档的简洁浅色风格实现。

后续如需 GitHub Pages，可将 `index.html`、`styles.css`、`app.js` 和 `assets/` 放到发布目录；不需要上传 `pages.md`、`tools/`、`preview.py` 或原始素材。

主图由 `tools/build_overview.py` 直接合成两份原始 PDF，输出 `assets/images/teacher-student-overview-hq.pdf` 和 6000 像素宽的 PNG；网页使用该 PNG，不使用用户截图。单行对比视频由 `tools/build_comparison_rows.py` 生成，处理记录见 `tools/comparison-row-manifest.json`。本次布局检查见 `tools/layout-qa.json`。
