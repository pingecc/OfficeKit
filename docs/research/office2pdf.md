# 调研：Word/Excel/PPT → PDF（2026-11-22）

## 候选对比

| 候选 | 结论 |
|---|---|
| **LibreOffice headless**（`soffice --convert-to pdf`） | ✅ 采用。保真度最高的开源方案，MPL-2.0，以独立子进程调用 |
| unoserver（unoconv 的现代后继） | 服务端阶段采用：LibreOffice 常驻进程、免逐次冷启动。桌面单机场景收益小，Phase 1 不引入（许可证以仓库为准） |
| docx2pdf | ❌ 依赖本机安装 MS Word（Windows COM / macOS AppleScript），把商业软件当运行时，不适合自有产品 |
| Pandoc | ❌ 走 LaTeX/HTML 中转，Office 版式保真不足 |
| Stirling-PDF（Web/Docker 工具箱） | 旁证：其 Office→PDF 后端同样是 LibreOffice。形态不匹配（Web 服务），桌面端不直接复用，可作为功能清单参考 |

## 决策

Phase 1 用 **soffice 子进程直接调用**，两个工程要点（踩坑预防）：

1. 每次调用使用独立 `-env:UserInstallation` 临时配置目录——避免与本机正在运行的 LibreOffice 抢占配置锁（headless 静默失败的常见原因）。
2. 同一输出目录的多个文件合并为一次调用，摊薄冷启动成本。

**桌面分发策略（后续再定）**：优先要求用户自装 LibreOffice / 引导下载；捆绑精简版体积过大，待商业模式明确后评估。

## 来源

- https://github.com/unoconv/unoserver
- https://github.com/Stirling-Tools/stirling-pdf
