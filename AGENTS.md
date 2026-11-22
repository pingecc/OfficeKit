# AGENTS.md — OfficeKit · Agent 协作约定

> 面向在本仓库工作的 AI Agent 与人类协作者。**开工前必读**；与 README.md 冲突时以本文件为准。

## 1. 项目是什么

**OfficeKit**——桌面端办公工具箱。目标：把 WPS 会员类文档能力逐步做成自有产品
（PDF→Word、Office→PDF、OCR、AI 写作、文档修复……），纯本地优先，功能按阶段上线。

- 当前状态与进度：`docs/roadmap.md`
- 每个功能的调研结论：`docs/research/<feature>.md`
- 架构说明：`docs/architecture.md`

## 2. 硬性规则（违反 = 返工）

### 2.1 先搜后写（No Reinventing Wheels）

实现任何新功能前，**必须**先检索 GitHub / PyPI / npm 是否已有成熟开源实现：

- 评估维度：维护状态（最近提交、issue 响应）、star 规模、**许可证**、中文支持、与本项目架构契合度
- 能复用现成库的，不自研；确实没有成熟方案才自己写
- 无论结论如何，都要写一份 `docs/research/<feature>.md`（检索了什么、候选对比、选了什么、为什么、许可证风险），并在本文件 §4 登记一行

### 2.2 许可证红线

- 任何新依赖，先查许可证并登记到 `LICENSES.md`
- GPL/AGPL 依赖仅限内部开发验证；**闭源商用分发前必须替换或取得商业授权**
- 当前已知风险：**PyMuPDF = AGPL-3.0**（pdf2docx 的底层依赖）

### 2.3 工程约定

- 引擎代码：Python ≥3.10，类型标注，pathlib，中文注释/报错，面向中文用户
- CLI 报错信息必须给出可执行的解决动作（如安装命令）
- 每个工具模块：docstring 写明用法与依赖；转换类必须有端到端测试（`engine/tests/`），测试自造样例文件、不依赖外部真实文件
- 新功能开发顺序：查资料 → 写 research 文档 → 实现模块 → 测试 → 更新 roadmap 与本文件 §4

## 3. 架构决策（已定，改动先讨论）

- **引擎**：`engine/` 下的 Python 包 `officekit`，CLI 入口 `officekit` / `python -m officekit`（短别名 `okit`）
- **桌面壳层（已定，2026-11-22）：Tauri 2**，代码在 `desktop/`。前端为 **React 18 + Arco Design + Vite**（源码 `desktop/src-ui/`，构建产物 `desktop/dist/`，npm 镜像走 npmmirror）；引擎经 PyInstaller 打包成 sidecar（officekit-engine），JSON-RPC over stdin/stdout 调用，协议文档在 `engine/officekit/serve.py` 模块头。改动壳层框架、前端框架或 sidecar 协议需先讨论；Windows 安装包走 `.github/workflows/build.yml`（Python sidecar 不可交叉编译）
- **未来接入方式**：引擎以 sidecar 进程接入壳层（JSON-RPC over stdin/stdout 或本地 socket）；设计模块时保持「输入路径 → 输出路径/结构化结果」的形态，方便包一层 RPC
- **AI 能力**（后续）：统一 OpenAI 兼容接口，供应商可切换，不绑死
- **产物目录**：`demo/` 放演示产物（已 gitignore）；测试样例由 `scripts/make_samples.py` 或测试内部自造

## 4. 依赖决策登记（先搜后写的结论索引，新条目追加在表格末尾）

| 日期 | 需求 | 结论 | 备选与理由 | 详见 |
|---|---|---|---|---|
| 2026-11-22 | PDF→Word | **pdf2docx**（MIT；底层依赖 PyMuPDF=AGPL） | 开源生态还原度最好（3.5k star）。⚠️ 上游已停止积极维护（Artifex 声明），出问题可转 fork 或自研 | `docs/research/pdf2word.md` |
| 2026-11-22 | Word/Excel/PPT→PDF | **LibreOffice headless** 外部进程调用（MPL-2.0） | docx2pdf 需本机装 MS Word；Pandoc 保真度不足；Stirling-PDF 的转换后端同样是 LibreOffice，佐证该路线 | `docs/research/office2pdf.md` |
