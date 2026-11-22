"""PyInstaller 打包入口：officekit-engine sidecar（服务模式）。

构建（仓库根目录执行）：
    .venv/bin/pyinstaller --onefile --name officekit-engine \
        --distpath desktop/src-tauri/binaries --workpath /tmp/officekit-pyi \
        --specpath /tmp/officekit-pyi -y scripts/engine_entry.py

然后把产物重命名为带 target-triple 的名字（Tauri sidecar 约定）：
    macOS (Apple Silicon): officekit-engine-aarch64-apple-darwin
    macOS (Intel):         officekit-engine-x86_64-apple-darwin
    Windows:               officekit-engine-x86_64-pc-windows-msvc.exe
"""
import sys

from officekit.cli import main

if __name__ == "__main__":
    sys.exit(main())
