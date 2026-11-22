# 路线图与状态

> 每完成一项：勾选，并附一行「日期 + 产出位置」。Agent 更新此处时同步 AGENTS.md §4。

## Phase 1 · 纯本地基础工具（当前阶段，零 API 成本）

- [x] PDF → Word —— 2026-11-22，`engine/kaiwu/pdf2word.py`，测试 `engine/tests/test_pdf2word.py`
- [x] Word/Excel/PPT → PDF —— 2026-11-22，`engine/kaiwu/office2pdf.py`，测试 `engine/tests/test_office2pdf.py`
- [ ] OCR 图片转文字（候选 PaddleOCR / RapidOCR，均为 Apache-2.0）
- [ ] Excel 批量工具（openpyxl 之上做工具层封装）
- [ ] PDF 合并/拆分/压缩（候选 pypdf，BSD）

## Phase 2 · AI 能力

- [ ] 翻译、AI 写作、摘要（统一 OpenAI 兼容接口，供应商可切换）
- [ ] AI 生成 PPT（LLM + python-pptx + 版式模板引擎）

## Phase 3 · 核心壁垒

- [ ] PDF→Word 高保真版面还原（自研版面分析，替换/增强 pdf2docx；顺带解决 PyMuPDF AGPL 风险）
- [ ] 文档修复（OOXML 修复，覆盖 .docx/.xlsx/.pptx 常见损坏）

## 桌面端（Tauri 2 · macOS / Windows）

- [x] 壳层选型 Tauri 2 + Python sidecar（JSON-RPC over stdin/stdout）—— 2026-11-22，`desktop/`；协议见 `engine/officekit/serve.py`
- [x] GUI 工具面板（PDF→Word、Office→PDF）接入引擎 serve 模式，serve 协议测试通过 —— 2026-11-22
- [x] macOS .app/.dmg 构建验证（Kaiwu.app 约 125MB + dmg 约 116MB，sidecar 随包）—— 2026-11-22
- [x] 前端重构 React 18 + Arco Design + Vite：拖拽上传、实时进度、结果卡片、错误兜底；修复对话框主线程死锁与 sidecar 运行时路径解析两个阻塞 bug —— 2026-11-22
- [ ] Windows 构建首跑（`.github/workflows/build.yml` 已就绪，需先建 GitHub 仓库）
- [ ] 双平台代码签名与自动更新（Tauri updater）

## Phase 4 · 生态（商业模式验证后再投）

- [ ] 云同步、模板市场（先解决内容授权）、团队协作
- [ ] 服务端批量版（Office→PDF 换 unoserver 常驻服务，避免逐次冷启动）
