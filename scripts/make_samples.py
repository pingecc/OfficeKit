"""生成演示用样例文件：report.docx（标题+段落+表格）、sales.xlsx（数据表）。

用法：.venv/bin/python scripts/make_samples.py [输出目录，默认 demo]
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from openpyxl import Workbook


def make_docx(path: Path) -> None:
    doc = Document()
    doc.add_heading("OfficeKit · 演示报告", level=0)
    doc.add_paragraph(
        "本文档由 OfficeKit 自动生成，用于演示 Word→PDF 与 PDF→Word 的完整转换链路。"
    )
    doc.add_heading("一、数据概览", level=1)
    table = doc.add_table(rows=4, cols=3)
    table.style = "Table Grid"
    heads = ["产品线", "Q3 营收（万元）", "Q4 营收（万元）"]
    rows = [
        ["文档工具", "1200", "1350"],
        ["转换服务", "860", "990"],
        ["AI 助手", "430", "720"],
    ]
    for col, head in enumerate(heads):
        table.rows[0].cells[col].text = head
    for r, row in enumerate(rows, start=1):
        for col, value in enumerate(row):
            table.rows[r].cells[col].text = value
    doc.add_heading("二、结论", level=1)
    doc.add_paragraph("工欲善其事，必先利其器。")
    doc.save(path)


def make_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "销售汇总"
    ws.append(["产品", "单价", "销量", "金额"])
    data = [
        ["标准版", 199, 320],
        ["专业版", 499, 120],
        ["旗舰版", 999, 45],
    ]
    for name, price, qty in data:
        ws.append([name, price, qty, price * qty])
    ws.append([])
    ws.append(["合计", None, None, sum(p * q for _, p, q in data)])
    wb.save(path)


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo")
    out_dir.mkdir(parents=True, exist_ok=True)
    make_docx(out_dir / "report.docx")
    make_xlsx(out_dir / "sales.xlsx")
    print(f"已生成样例：{out_dir / 'report.docx'}、{out_dir / 'sales.xlsx'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
