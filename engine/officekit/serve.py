"""JSON-RPC over stdin/stdout —— 引擎服务模式（sidecar 协议）。

供桌面壳层（Tauri）以子进程方式调用：壳层启动本进程、逐行写请求、逐行读响应。

协议（每行一个 JSON 对象，UTF-8）：
    请求：{"id": <int>, "method": "<str>", "params": {...}}
    响应：{"id": <int>, "ok": true, "result": {...}} | {"id": <int>, "ok": false, "error": "<str>"}
    事件（无 id，主动推送）：{"event": "progress", "percent": 0-100, "message": "<str>"}
        percent / message 均可缺省；缺 percent 时下游不应推进进度条。

方法：
    ping        → {"version": "...", "soffice": bool}
    pdf2word    params {input, output?, pages?}  → {"output": "<path>"}
    office2pdf  params {inputs: [...], outdir?}  → {"results": [...]}

约定：stdout 只允许输出 JSON 行（进度事件与响应都走 stdout）；诊断信息走 stderr。
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

from . import __version__, office2pdf, pdf2word

__all__ = ["serve"]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _emit_progress(message: str = "", percent: int | float | None = None) -> None:
    payload: dict = {"event": "progress"}
    if percent is not None:
        payload["percent"] = max(0, min(100, round(percent)))
    if message:
        payload["message"] = _ANSI_RE.sub("", message)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


class JsonProgressHandler(logging.Handler):
    """兜底日志通道：把记录转成仅含 message 的进度事件（不推进进度条）。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            _emit_progress(message=self.format(record))
        except Exception:  # 日志永不打断业务
            pass


class Pdf2WordProgressHandler(logging.Handler):
    """解析 pdf2docx 的阶段日志，映射为 0-100 结构化进度。

    pdf2docx 日志形态："[1/4] Opening document..." / "(1/3) Page 1" / "Terminated in 0.5s."
    映射：打开 8% → 分析 20% → 解析 30-70%（按页推进）→ 生成 75-100%（按页推进）。
    """

    PHASES = {"[1/4]": 8, "[2/4]": 20, "[3/4]": 30, "[4/4]": 75}
    PAGE_RE = re.compile(r"\((\d+)/(\d+)\)")

    def __init__(self) -> None:
        super().__init__()
        self.phase = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            percent, self.phase = self.map(msg, self.phase)
            if percent is not None:
                _emit_progress(percent=percent, message=msg)
        except Exception:  # 进度永不打断业务
            pass

    def map(self, msg: str, phase: int) -> tuple[int | float | None, int]:
        for marker, percent in self.PHASES.items():
            if marker in msg:
                return percent, int(marker[1])
        m = self.PAGE_RE.search(msg)
        if m and phase == 3:
            i, n = int(m.group(1)), int(m.group(2))
            return 30 + 40 * (i - 1) / max(n, 1), phase
        if m and phase == 4:
            i, n = int(m.group(1)), int(m.group(2))
            return 75 + 25 * (i - 1) / max(n, 1), phase
        return None, phase


def _handle(method: str, params: dict):
    if method == "ping":
        return {"version": __version__, "soffice": bool(office2pdf.find_soffice())}

    if method == "pdf2word":
        pdf_logger = logging.getLogger("pdf2docx")
        handler = Pdf2WordProgressHandler()
        pdf_logger.addHandler(handler)
        pdf_logger.propagate = False  # 防止根日志处理器重复发事件
        try:
            output = pdf2word.convert(params["input"], params.get("output"), params.get("pages"))
        finally:
            pdf_logger.removeHandler(handler)
            pdf_logger.propagate = True
        _emit_progress(percent=100, message="转换完成")
        return {"output": str(output)}

    if method == "office2pdf":
        inputs = params["inputs"]
        total = len(inputs)

        def report(done: int, current) -> None:
            if total:
                _emit_progress(
                    percent=round(done / total * 100),
                    message=f"{done}/{total} · {Path(current).name}",
                )

        results = office2pdf.convert(inputs, params.get("outdir"), progress_cb=report)
        _emit_progress(percent=100, message="转换完成")
        return {
            "results": [
                {
                    "input": str(r["input"]),
                    "ok": r["ok"],
                    "output": str(r["output"]) if r["ok"] else None,
                    "error": r["error"],
                }
                for r in results
            ]
        }

    raise ValueError(f"未知方法：{method!r}")


def serve() -> int:
    """阻塞式服务循环；stdin 关闭（EOF）时退出。"""
    logging.basicConfig(
        level=logging.INFO,
        handlers=[JsonProgressHandler()],
        format="%(message)s",
        force=True,
    )
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req_id = None
        try:
            request = json.loads(line)
            req_id = request.get("id")
            result = _handle(request.get("method", ""), request.get("params") or {})
            response = {"id": req_id, "ok": True, "result": result}
        except Exception as exc:  # noqa: BLE001 —— 协议层兜底：错误也必须回成 JSON
            response = {"id": req_id, "ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0
