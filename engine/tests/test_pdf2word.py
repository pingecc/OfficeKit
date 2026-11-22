"""pdf2word 模块测试：用 PyMuPDF 自造 PDF 样例，不依赖外部文件。"""
import pymupdf
import pytest
from docx import Document

from officekit.pdf2word import convert, parse_pages


def _save_text_pdf(path, lines: list[str]) -> None:
    """每行文本生成一页（使用 PyMuPDF 内置中文字体 china-s）。"""
    doc = pymupdf.open()
    for text in lines:
        page = doc.new_page()
        page.insert_text((72, 120), text, fontname="china-s", fontsize=16)
    doc.save(path)
    doc.close()


def _docx_text(path) -> str:
    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def test_parse_pages():
    assert parse_pages("1-3,5", 10) == [0, 1, 2, 4]
    assert parse_pages("2", 10) == [1]
    assert parse_pages("2，3", 10) == [1, 2]  # 中文逗号


def test_parse_pages_invalid():
    with pytest.raises(ValueError):
        parse_pages("5-2", 10)  # 区间倒序
    with pytest.raises(ValueError):
        parse_pages("99", 1)  # 全部超界


def test_roundtrip_text(tmp_path):
    pdf = tmp_path / "sample.pdf"
    _save_text_pdf(pdf, ["超级工具箱测试文档 Alpha 123", "第二页 Beta"])

    out = convert(pdf)  # 缺省输出：同名 .docx
    assert out.name == "sample.docx"
    assert out.exists() and out.stat().st_size > 0
    assert "Alpha" in _docx_text(out)


def test_pages_filter(tmp_path):
    pdf = tmp_path / "multi.pdf"
    _save_text_pdf(pdf, ["PAGE-A", "PAGE-B", "PAGE-C"])

    out = convert(pdf, pages_spec="2")  # 只转第 2 页
    text = _docx_text(out)
    assert "PAGE-B" in text
    assert "PAGE-A" not in text


def test_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert(tmp_path / "nope.pdf")
