# 调研：PDF → Word（2026-11-22）

## 检索范围

GitHub / PyPI：pdf2docx 及其 fork 生态、Stirling-PDF（旁证）、LibreOffice 直接转换、商业引擎对标。

## 候选对比

| 候选 | 结论 |
|---|---|
| **pdf2docx**（ArtifexSoftware/pdf2docx，原 dothinking/pdf2docx） | ✅ 采用。约 3.5k star，**MIT 许可**；原理：PyMuPDF 抽取 PDF 数据 → 规则解析版面（段落/表格/字体/图片）→ python-docx 生成 docx。⚠️ README 声明「不再由 Artifex 积极维护」，仓库保留、接受 PR/fork |
| pdf2docx fork（embiem/pdf2docx-headless、mithunvoe/pdf2docx-plus 等） | 备用。主库出问题时可切换 |
| LibreOffice PDF 导入 → 导出 docx | ❌ 还原度差（Stirling-PDF 社区同样反馈其 LibreOffice 路线转换 Word 效果一般），仅适合粗转换 |
| 商业引擎（Solid Documents / Adobe / WPS 自有） | 效果最好，闭源收费；作为 Phase 3 自研版面分析的对标 |

## 决策

采用 **pdf2docx**。风险与后续动作：

1. **许可证**：pdf2docx 本体 MIT（已核实仓库），但其底层依赖 **PyMuPDF 为 AGPL-3.0** —— 闭源商用分发前需替换（候选：pypdfium2，宽松许可）或购买 Artifex 商业授权。已登记 `LICENSES.md`。
2. **维护**：上游停更 → 长期计划（Phase 3）自研版面分析做高保真转换；保持 `pdf2word.convert()` 接口不变，替换实现时上层无感。
3. **已知局限**：复杂多栏/表格嵌套还原度下降；扫描件无 OCR（Phase 1 后续接 OCR 模块后可先 OCR 再转换）。

## 来源

- https://github.com/ArtifexSoftware/pdf2docx （原 dothinking/pdf2docx，已迁移）
- https://github.com/Stirling-Tools/stirling-pdf （旁证）
