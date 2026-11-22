"""OfficeKit 命令行入口。

    officekit --version
    officekit pdf2word in.pdf [-o out.docx] [--pages 1-5,8]
    officekit office2pdf a.docx b.xlsx [-o outdir] [--timeout 300]
    officekit serve          # JSON-RPC 服务模式（桌面壳层 sidecar 协议）

短别名：okit。约定：逐文件报告、失败不中断；全部成功退出码 0，否则 1。
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__, office2pdf, pdf2word

log = logging.getLogger("officekit")


def cmd_pdf2word(args: argparse.Namespace) -> int:
    inputs = [Path(p) for p in args.inputs]
    # -o 语义：单输入且以 .docx 结尾 → 目标文件；否则视为输出目录
    out_file = (
        Path(args.output)
        if args.output and len(inputs) == 1 and args.output.lower().endswith(".docx")
        else None
    )
    out_dir = Path(args.output) if (args.output and out_file is None) else None

    ok = fail = 0
    for src in inputs:
        try:
            dst = out_file
            if dst is None and out_dir is not None:
                dst = out_dir / f"{src.stem}.docx"
            path = pdf2word.convert(src, dst, pages_spec=args.pages)
            print(f"✅ {src} -> {path}")
            ok += 1
        except Exception as exc:  # noqa: BLE001 —— CLI 层兜底，逐文件报告不中断
            print(f"❌ {src}: {exc}", file=sys.stderr)
            fail += 1
    log.info("pdf2word 完成：%d 成功，%d 失败", ok, fail)
    return 1 if fail else 0


def cmd_office2pdf(args: argparse.Namespace) -> int:
    try:
        results = office2pdf.convert(args.inputs, outdir=args.output, timeout=args.timeout)
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    for r in results:
        if r["ok"]:
            print(f"✅ {r['input']} -> {r['output']}")
        else:
            print(f"❌ {r['input']}: {r['error']}", file=sys.stderr)
    ok = sum(r["ok"] for r in results)
    log.info("office2pdf 完成：%d 成功，%d 失败", ok, len(results) - ok)
    return 0 if ok == len(results) else 1


def cmd_serve(args: argparse.Namespace) -> int:
    from .serve import serve

    return serve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="officekit",
        description="OfficeKit —— 办公工具箱 · 文档处理引擎",
    )
    parser.add_argument("--version", action="version", version=f"officekit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pdf2word", help="PDF 转 Word(.docx)，支持页码范围")
    p.add_argument("inputs", nargs="+", help="PDF 文件（可多个）")
    p.add_argument("-o", "--output", help="输出 .docx 文件或目录，默认与源文件同目录同名")
    p.add_argument("--pages", help="页码范围（从 1 开始），如 1-5,8；缺省全部页")
    p.set_defaults(func=cmd_pdf2word)

    p = sub.add_parser(
        "office2pdf", help="Word/Excel/PPT 转 PDF（需本机安装 LibreOffice）"
    )
    p.add_argument("inputs", nargs="+", help=".docx/.doc/.xlsx/.xls/.pptx/.ppt 文件（可多个）")
    p.add_argument("-o", "--output", help="输出目录，默认各自输出到源文件所在目录")
    p.add_argument("--timeout", type=int, default=300, help="单批转换超时秒数（默认 300）")
    p.set_defaults(func=cmd_office2pdf)

    p = sub.add_parser("serve", help="以 JSON-RPC 服务模式运行（桌面壳层 sidecar 协议）")
    p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
