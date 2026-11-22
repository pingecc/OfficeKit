"""PDF → Word(.docx) 转换。

依赖与许可：pdf2docx（MIT）；其底层依赖 PyMuPDF 为 AGPL-3.0，
闭源商用分发前需替换或取得商业授权（见仓库根 LICENSES.md）。

用法：
    from officekit import pdf2word
    pdf2word.convert("in.pdf", "out.docx", pages_spec="1-5,8")   # 页码 1-based

CLI：officekit pdf2word in.pdf [-o out.docx] [--pages 1-5,8]

调研记录：docs/research/pdf2word.md
"""
from __future__ import annotations

import logging
from pathlib import Path

import pymupdf  # PyMuPDF：读页数/校验页码（pdf2docx 的底层依赖）
from pdf2docx import Converter

log = logging.getLogger(__name__)

__all__ = ["convert", "parse_pages"]


def parse_pages(spec: str, page_count: int) -> list[int]:
    """把 ``1-3,5`` 这类页码串解析成 pdf2docx 需要的 0-based 页序列。

    支持中英文逗号分隔；``1-3`` 表示第 1 到第 3 页（含端点）。
    超出总页数的页码忽略并告警；解析结果为空则抛 ValueError。
    """
    pages: set[int] = set()
    for part in spec.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start < 1 or end < start:
                raise ValueError(f"页码区间非法：{part!r}（应为 1-3 这样的升序区间）")
            pages.update(range(start - 1, end))
        else:
            n = int(part)
            if n < 1:
                raise ValueError(f"页码必须从 1 开始：{part!r}")
            pages.add(n - 1)

    kept = sorted(p for p in pages if p < page_count)
    dropped = sorted(p + 1 for p in pages if p >= page_count)
    if dropped:
        log.warning("页码超出总页数 %d，已忽略：%s", page_count, dropped)
    if not kept:
        raise ValueError(f"页码 {spec!r} 均超出文档总页数 {page_count}")
    return kept


def convert(
    pdf_path: str | Path,
    docx_path: str | Path | None = None,
    pages_spec: str | None = None,
) -> Path:
    """把 PDF 转成可编辑的 .docx。

    Args:
        pdf_path: 源 PDF 路径。
        docx_path: 输出路径；缺省与源文件同名、扩展名改为 .docx。
        pages_spec: 页码范围（1 开始），如 ``1-3,5``；None 表示全部页。
    Returns:
        生成的 .docx 路径。
    """
    src = Path(pdf_path)
    if not src.exists():
        raise FileNotFoundError(f"找不到源文件：{src}")
    dst = Path(docx_path) if docx_path else src.with_suffix(".docx")

    with pymupdf.open(src) as doc:
        page_count = doc.page_count

    converter = Converter(str(src))
    try:
        kwargs: dict = {}
        if pages_spec:
            kwargs["pages"] = parse_pages(pages_spec, page_count)
        converter.convert(str(dst), **kwargs)
    finally:
        converter.close()

    log.info("PDF→Word 完成：%s -> %s（共 %d 页）", src, dst, page_count)
    return dst
