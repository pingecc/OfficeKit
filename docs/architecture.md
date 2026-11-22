# 架构

## 总体形态（v1，2026-11-22）

```
OfficeKit.app / OfficeKit.exe    desktop/ —— Tauri 2 壳层（Rust，安装包小）
  ├── src-ui/          React 18 + Arco Design（Vite 构建到 desktop/dist）
  ├── src-tauri/       Rust：文件对话框、打开路径、sidecar 编排（src/lib.rs）
  └── sidecar          officekit-engine（PyInstaller 单文件）
        └── JSON-RPC over stdin/stdout（协议见 engine/officekit/serve.py 模块文档）
              ├── pdf2word     pdf2docx（MIT）+ PyMuPDF（AGPL，商用前替换）
              └── office2pdf   LibreOffice (soffice) 子进程
```

- 壳层不实现任何文档逻辑，只做「选文件 → 调引擎 → 展示结果」。
- 引擎与 UI 无关：CLI（`officekit` 命令，短别名 `okit`）与 serve 模式共用同一套模块函数。

## sidecar 协议（v1）

- 每行一个 JSON（UTF-8）：
  - 请求 `{"id": <int>, "method": <str>, "params": {...}}`
  - 响应 `{"id", "ok": true, "result"}` / `{"id", "ok": false, "error"}`
  - 进度事件（无 id，主动推）`{"event": "progress", "percent": 0-100, "message": "..."}`——percent/message 均可缺省；pdf2word 由 pdf2docx 阶段日志映射（打开 8% → 分析 20% → 解析 30-70% → 生成 75-100%），office2pdf 按完成数推进（soffice 批量内部无法观察单文件粒度）
- stdout 只允许 JSON 行；诊断信息走 stderr（壳层转发为 `engine-stderr` 事件）。
- v1 模型：**每次转换拉起一个 sidecar 进程**（损耗约 1-2s 启动）。出现高频小请求场景后再演进为常驻会话。
- 打包：PyInstaller 需 `--paths engine`（editable 安装的 import hook 不被识别）；产物按 Tauri 约定重命名为 `<name>-<target-triple>`。

## 工程要点（踩坑记录）

- **Tauri 文件对话框绝不能用 `blocking_*` 变体**：macOS 上同步命令在主线程的 IPC 分发中执行，`blocking_pick_files()` 会等待一个只能在主线程打开的对话框 → 死锁，整个应用卡死（hang 报告卡在 `blocking_pick_files`）。对话框命令必须 async + 回调式 API + oneshot 通道（见 `desktop/src-tauri/src/lib.rs`）。
- **sidecar 运行时路径 ≠ 打包路径**：`tauri-plugin-shell` 的 `sidecar(name)` 按 `current_exe 目录/name` 原样拼接（源码 `relative_command_path`），而打包器会把 `externalBin: ["binaries/officekit-engine"]` **展平**到 `Contents/MacOS/officekit-engine`——传带 `binaries/` 前缀的名字必 ENOENT。运行时按候选列表 `["officekit-engine", "binaries/officekit-engine"]` 逐个解析。
- **一次性请求必须主动 kill 引擎**：serve 模式是常驻循环，转换完不会自己退出；壳层若只等 `Terminated` 事件会永远等待（现象：转换实际成功、前端一直转圈）。收到响应后立即 `child.kill()`，并给命令加 `kill_on_drop(true)` 兜底。
- **JSON 通道里必须剥 ANSI 码**：pdf2docx 等下游库的日志带 `\x1b[1;36m` 颜色码，`serve.py` 的进度通道统一 `_ANSI_RE` 清理。
- soffice 每次调用用独立 `-env:UserInstallation` 临时配置目录，避免与本机正在运行的 LibreOffice 抢锁。
- 同一输出目录的多文件合并为一次 soffice 调用；同目录 stem 相同的文件（a.docx + a.xlsx）输出会互相覆盖 → 逐个转换并重命名 `<stem>-<ext>.pdf`；每次转换前预清理同名残留产物，避免失败被误判为成功（回归测试覆盖）。
- 国内网络镜像策略：rustup → USTC rust-static；LibreOffice → USTC tdf；crates.io → rsproxy（desktop/.cargo/config.toml）；npm → npmmirror。
- Windows 构建走 `.github/workflows/build.yml`（Python sidecar 无法从 macOS 交叉编译，三平台矩阵各自打包）。

## 演进方向

1. **AI 能力**（Phase 2）：引擎加 OpenAI 兼容 client，供应商可切换（DeepSeek / GLM / 通义），GUI 加 AI 面板。
2. **服务端批量版**：复用同一引擎；Office→PDF 届时换 [unoserver](https://github.com/unoconv/unoserver)（LibreOffice 常驻服务）。
3. **桌面分发**：Office 转 PDF 的「一键安装 LibreOffice」引导、双平台代码签名、自动更新（Tauri updater）、捆绑精简版 LibreOffice（远期）。
