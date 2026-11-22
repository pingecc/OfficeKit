# 依赖许可证登记

> 规则（AGENTS.md §2.2）：GPL/AGPL 依赖仅限内部开发验证；**闭源商用分发前必须替换或取得商业授权**。
> 新增依赖必须在此追加一行，并同步 `docs/research/<feature>.md`。

| 依赖 | 版本 | 许可证 | 用途 | 商用风险与动作 |
|---|---|---|---|---|
| pdf2docx | 0.5.x | MIT（Artifex 于停止维护时重新以 MIT 发布，已核实） | PDF→Word 主引擎 | 低 |
| PyMuPDF (fitz) | 随 pdf2docx | **AGPL-3.0** | pdf2docx 底层 PDF 解析；本引擎亦用于读页数/页码校验 | **高**：闭源商用需购买 Artifex 商业授权，或替换为 pypdfium2（宽松许可）并重写依赖面 |
| python-docx | ≥1.1 | MIT | 测试样例构造、docx 内容校验 | 低 |
| openpyxl | ≥3.1 | MIT | 测试样例构造 | 低 |
| pytest | ≥8 | MIT | 测试框架（仅 dev 依赖） | 低 |
| LibreOffice（外部进程调用） | 本机安装 | MPL-2.0 | Word/Excel/PPT → PDF 转换后端 | 低：以独立子进程调用、不修改不链接其代码；未来若捆绑分发需履行 MPL 通知义务 |
| PyInstaller | ≥6.10 | GPLv2 + 特殊例外（明确允许分发其产出的二进制） | 打包 officekit-engine sidecar（仅构建期） | 低 |
| Pillow | ≥11.0 | MIT-CMU | 生成应用图标源图（仅构建期） | 低 |
| Tauri 2 及插件 crates | 2.x | MIT / Apache-2.0 双许可 | 桌面壳层（desktop/src-tauri） | 低 |

登记日期：2026-11-22
