"""office2pdf 模块测试：自造 docx/xlsx 样例，端到端走 soffice（未装 LibreOffice 时跳过）。"""
import pymupdf
import pytest
from docx import Document
from openpyxl import Workbook

from officekit.office2pdf import convert


def _make_docx(path) -> None:
    doc = Document()
    doc.add_heading("季度经营报告", level=1)
    doc.add_paragraph("本报告由 OfficeKit 自动生成，用于端到端测试。")
    table = doc.add_table(rows=2, cols=3)
    table.style = "Table Grid"
    for col, head in enumerate(["项目", "Q3", "Q4"]):
        table.rows[0].cells[col].text = head
    for col, value in enumerate(["营收", "1200", "1350"]):
        table.rows[1].cells[col].text = value
    doc.save(path)


def _make_xlsx(path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "汇总"
    ws.append(["产品", "销量"])
    ws.append(["扳手", 100])
    ws.append(["锤子", 80])
    wb.save(path)


def test_docx_and_xlsx_to_pdf(tmp_path, soffice):
    docx = tmp_path / "report.docx"
    xlsx = tmp_path / "sales.xlsx"
    _make_docx(docx)
    _make_xlsx(xlsx)

    results = convert([docx, xlsx])  # 缺省输出到各自源文件目录
    assert all(r["ok"] for r in results), results

    assert "季度经营报告" in pymupdf.open(tmp_path / "report.pdf")[0].get_text()
    assert "扳手" in pymupdf.open(tmp_path / "sales.pdf")[0].get_text()


def test_batch_and_outdir(tmp_path, soffice):
    docx = tmp_path / "src" / "a.docx"
    docx.parent.mkdir()
    _make_docx(docx)

    out = tmp_path / "pdf"
    results = convert([docx], outdir=out)
    assert results[0]["ok"], results
    assert (out / "a.pdf").exists()


def test_same_stem_no_overwrite(tmp_path, soffice):
    """回归：同目录 a.docx + a.xlsx 不得互相覆盖产物（<stem>-<ext>.pdf）。"""
    docx = tmp_path / "a.docx"
    xlsx = tmp_path / "a.xlsx"
    _make_docx(docx)
    _make_xlsx(xlsx)

    results = convert([docx, xlsx])
    assert all(r["ok"] for r in results), results
    assert len({r["output"] for r in results}) == 2  # 两个不同产物
    assert "季度经营报告" in pymupdf.open(tmp_path / "a-docx.pdf")[0].get_text()
    assert "扳手" in pymupdf.open(tmp_path / "a-xlsx.pdf")[0].get_text()


def test_stale_output_not_mask_failure(tmp_path, soffice):
    """回归：目录里预先存在的同名 PDF 不能让失败被误判为成功。"""
    docx = tmp_path / "b.docx"
    _make_docx(docx)
    stale = tmp_path / "b.pdf"
    stale.write_bytes(b"not really a pdf")  # 预清理后此文件应被重写为真 PDF

    results = convert([docx])
    assert results[0]["ok"], results
    assert pymupdf.open(stale).page_count >= 1  # 已被真实产物替换


def test_unsupported_suffix(tmp_path, soffice):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    with pytest.raises(ValueError):
        convert([f])


def test_missing_file(tmp_path, soffice):
    with pytest.raises(FileNotFoundError):
        convert([tmp_path / "no.docx"])
