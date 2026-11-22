"""Word/Excel/PPT → PDF：调用本机 LibreOffice（soffice）headless 转换。

依赖与许可：LibreOffice（MPL-2.0），以独立子进程调用，不修改不链接其代码。
若未安装：
    macOS:   brew install --cask libreoffice
    Windows: https://www.libreoffice.org/download 下载安装（soffice.exe 在默认路径或 PATH 即可）
    Linux:   sudo apt install libreoffice

用法：
    from officekit import office2pdf
    results = office2pdf.convert(["a.docx", "b.xlsx"], outdir="out/")
    # results: [{"input": Path, "ok": bool, "output": Path|None, "error": str|None}, ...]

CLI：officekit office2pdf a.docx b.xlsx [-o outdir] [--timeout 300]

调研记录：docs/research/office2pdf.md
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path

__all__ = ["convert", "find_soffice", "SUPPORTED_SUFFIXES"]

SUPPORTED_SUFFIXES = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}

_SOFFICE_CANDIDATES = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/local/bin/soffice",
    "/usr/bin/soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
)

INSTALL_HINT = (
    "未找到 LibreOffice (soffice)。请先安装：\n"
    "  macOS:   brew install --cask libreoffice\n"
    "  Windows: https://www.libreoffice.org/download 下载安装\n"
    "  Linux:   sudo apt install libreoffice"
)


def find_soffice() -> str | None:
    """定位 soffice 可执行文件；找不到返回 None。"""
    found = shutil.which("soffice")
    if found:
        return found
    for candidate in _SOFFICE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def convert(
    inputs: list[str | Path],
    outdir: str | Path | None = None,
    timeout: int = 300,
    progress_cb: Callable[[int, Path], None] | None = None,
) -> list[dict]:
    """批量把 Office 文档转成 PDF。

    同一输出目录的文件合并为一次 soffice 调用（LibreOffice 冷启动慢，合并更快）。
    使用独立 UserInstallation 配置目录，避免与本机正在运行的 LibreOffice 互相锁死。
    同目录下 stem 相同的文件（如 a.docx 与 a.xlsx）会让 soffice 输出同名 PDF 互相覆盖，
    因此逐个转换并把产物重命名为 ``<stem>-<ext>.pdf``。

    Args:
        inputs: 源文件列表（.docx/.doc/.xlsx/.xls/.pptx/.ppt）。
        outdir: 输出目录；None 时各自输出到源文件所在目录。
        timeout: 单批转换超时（秒）。
        progress_cb: 可选，进度回调 ``progress_cb(已完成数, 当前文件 Path)``；
            注意 soffice 批量转换内部无法观察单文件粒度，回调按"组"推进。
    Returns:
        每个输入一条结果：{"input", "ok", "output", "error"}。
    """
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(INSTALL_HINT)

    sources: list[Path] = []
    for raw in inputs:
        p = Path(raw)
        if not p.exists():
            raise FileNotFoundError(f"找不到源文件：{p}")
        if p.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(
                f"不支持的格式 {p.suffix!r}（支持：{sorted(SUPPORTED_SUFFIXES)}）：{p}"
            )
        sources.append(p)

    total = len(sources)
    if progress_cb and total:
        progress_cb(0, sources[0])

    # 按输出目录分组，一组一次 soffice 调用
    groups: dict[Path, list[Path]] = {}
    for p in sources:
        target = Path(outdir) if outdir else p.parent
        groups.setdefault(target, []).append(p)

    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="officekit-lo-profile-") as profile:
        profile_uri = Path(profile).resolve().as_uri()
        for target, files in groups.items():
            target.mkdir(parents=True, exist_ok=True)
            stem_counts = Counter(f.stem for f in files)
            batch = [f for f in files if stem_counts[f.stem] == 1]
            colliding = [f for f in files if stem_counts[f.stem] > 1]
            if batch:
                results.extend(_run_batch(soffice, profile_uri, target, batch, timeout))
            for f in colliding:
                out_name = f"{f.stem}-{f.suffix.lstrip('.')}.pdf"
                results.extend(
                    _run_batch(soffice, profile_uri, target, [f], timeout, out_names=[out_name])
                )
            if progress_cb:
                progress_cb(len(results), files[-1])
    return results


def _run_batch(
    soffice: str,
    profile_uri: str,
    target: Path,
    files: list[Path],
    timeout: int,
    out_names: list[str] | None = None,
) -> list[dict]:
    """跑一次 soffice 转换并核对产物；out_names 与 files 等长，None 用默认 <stem>.pdf。"""
    out_names = out_names or [f"{f.stem}.pdf" for f in files]
    # 预清理：上次运行残留的产物会让本次失败被误判为成功
    for stale in {target / f"{f.stem}.pdf" for f in files} | {target / n for n in out_names}:
        stale.unlink(missing_ok=True)

    cmd = [
        soffice,
        f"-env:UserInstallation={profile_uri}",
        "--headless", "--norestore", "--nologo", "--nolockcheck",
        "--convert-to", "pdf",
        "--outdir", str(target),
        *[str(f) for f in files],
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return [_fail(f, f"转换超时（>{timeout}s）") for f in files]

    results: list[dict] = []
    for f, name in zip(files, out_names):
        # soffice 对个别损坏文件可能仍退出 0，成败以产物是否存在为准
        produced = target / f"{f.stem}.pdf"
        final = target / name
        if produced.exists():
            if final != produced:
                produced.replace(final)
            results.append({"input": f, "ok": True, "output": final, "error": None})
        else:
            results.append(_fail(f, "soffice 未产出 PDF（源文件可能损坏或加密）"))
    return results


def _fail(src: Path, reason: str) -> dict:
    return {"input": src, "ok": False, "output": None, "error": reason}
