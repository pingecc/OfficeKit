"""serve 服务模式（sidecar 协议）测试：子进程 + 管道全链路。"""
import json
import subprocess
import sys

import pytest

from officekit import __version__


@pytest.fixture()
def engine():
    proc = subprocess.Popen(
        [sys.executable, "-m", "officekit", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    yield proc
    proc.stdin.close()
    proc.wait(timeout=10)


def _request(proc, **body):
    """发送一条请求并读响应；跳过中间穿插的进度事件行。"""
    proc.stdin.write(json.dumps(body, ensure_ascii=False) + "\n")
    proc.stdin.flush()
    while True:
        line = proc.stdout.readline()
        assert line, "引擎进程意外退出"
        obj = json.loads(line)
        if "event" not in obj:
            return obj


def test_ping(engine):
    resp = _request(engine, id=1, method="ping", params={})
    assert resp["id"] == 1 and resp["ok"]
    assert resp["result"]["version"] == __version__
    assert isinstance(resp["result"]["soffice"], bool)


def test_pdf2word_over_rpc(tmp_path, engine):
    from test_pdf2word import _save_text_pdf  # 复用样例构造

    pdf = tmp_path / "rpc.pdf"
    _save_text_pdf(pdf, ["RPC round trip 你好 123"])
    resp = _request(engine, id=2, method="pdf2word", params={"input": str(pdf)})
    assert resp["ok"], resp
    assert resp["result"]["output"].endswith("rpc.docx")
    assert (tmp_path / "rpc.docx").exists()


def test_unknown_method(engine):
    resp = _request(engine, id=3, method="nope", params={})
    assert not resp["ok"]
    assert "未知方法" in resp["error"]


def test_bad_json(engine):
    engine.stdin.write("not json\n")
    engine.stdin.flush()
    resp = json.loads(engine.stdout.readline())
    assert not resp["ok"]


def test_pdf_progress_mapping():
    """pdf2docx 阶段日志 → 0-100 进度的映射规则。"""
    from officekit.serve import Pdf2WordProgressHandler

    h = Pdf2WordProgressHandler()
    p, phase = h.map("[3/4] Parsing pages...", 0)
    assert (p, phase) == (30, 3)
    p, phase = h.map("(2/5) Page 2", phase)
    assert p == 30 + 40 / 5
    p, phase = h.map("[4/4] Creating pages...", phase)
    assert (p, phase) == (75, 4)
    p, _ = h.map("(5/5) Page 5", phase)
    assert p == 75 + 25 * 4 / 5
    p, _ = h.map("'created' timestamp seems very low", phase)
    assert p is None  # 无关日志不推进进度


def test_progress_events_strip_ansi(tmp_path, engine):
    """进度事件里的 ANSI 颜色码必须被剥掉（pdf2docx 日志带色）。"""
    from test_pdf2word import _save_text_pdf
    from officekit.serve import _ANSI_RE

    assert _ANSI_RE.sub("", "\x1b[1;36m[1/4] Opening\x1b[0m") == "[1/4] Opening"

    pdf = tmp_path / "ansi.pdf"
    _save_text_pdf(pdf, ["ansi test 1"])
    proc_in = json.dumps({"id": 9, "method": "pdf2word", "params": {"input": str(pdf)}}) + "\n"
    engine.stdin.write(proc_in)
    engine.stdin.flush()
    seen_event, got_response = False, False
    while not (seen_event and got_response):
        line = engine.stdout.readline()
        assert line, "引擎进程意外退出"
        obj = json.loads(line)
        if "event" in obj:
            seen_event = True
            assert "\x1b" not in obj["message"], obj["message"]
        else:
            got_response = obj.get("id") == 9 and obj["ok"]
    assert seen_event and got_response
