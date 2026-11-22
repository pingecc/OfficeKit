#!/usr/bin/env bash
# 重打引擎 sidecar 并放到 Tauri 约定位置（当前平台）。
# 用途：改了 engine/ 下的 Python 代码后，要在 GUI（tauri dev / 打包版）里验证时执行。
# tauri dev 运行中时执行本脚本：下一次转换即使用新引擎，无需重启应用。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYI="$ROOT/.venv/bin/pyinstaller"
EXT=""; [ "$(uname)" = "Windows" ] && EXT=".exe"

[ -x "$PYI" ] || { echo "未找到 .venv/bin/pyinstaller。先执行：python3 -m venv .venv && .venv/bin/pip install -e 'engine[dev]'"; exit 1; }
TRIPLE="$(rustc -vV 2>/dev/null | awk '/^host/ {print $2}')"
[ -n "${TRIPLE:-}" ] || { echo "未找到 rustc：需要 Rust 工具链（rustup install）；或手动改写本脚本里的目标三元组"; exit 1; }

OUT="$ROOT/desktop/src-tauri/binaries"
mkdir -p "$OUT"
"$PYI" --onefile --name officekit-engine --paths "$ROOT/engine" \
  --distpath "$OUT" --workpath /tmp/officekit-pyi --specpath /tmp/officekit-pyi -y \
  "$ROOT/scripts/engine_entry.py"
mv "$OUT/officekit-engine$EXT" "$OUT/officekit-engine-$TRIPLE$EXT"
echo "sidecar 已更新：$OUT/officekit-engine-$TRIPLE$EXT"

# 同步到 dev 运行目录：tauri dev 的引擎是 target/debug/officekit-engine（构建时复制过去），
# 直接覆盖后，下一次转换即用新引擎，无需重启 dev
DEV_BIN="$ROOT/desktop/src-tauri/target/debug/officekit-engine$EXT"
if [ -d "$(dirname "$DEV_BIN")" ]; then
  cp "$OUT/officekit-engine-$TRIPLE$EXT" "$DEV_BIN"
  echo "已同步到 dev 运行目录：$DEV_BIN（tauri dev 下一次转换即生效）"
fi
