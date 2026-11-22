# OfficeKit

> 办公工具箱——把常用的办公能力，装进一个桌面应用。
> 纯本地处理，文件不出电脑。

桌面端办公工具箱（macOS / Windows），逐步实现 PDF 转换、OCR、AI 写作等能力，对标 WPS 会员类功能。

**给 AI Agent 的协作规则在 [AGENTS.md](AGENTS.md)，开工前必读。**

## 当前功能

| 命令 | 功能 | 状态 |
|---|---|---|
| `officekit pdf2word` | PDF → Word(.docx)，支持页码范围 | ✅ |
| `officekit office2pdf` | Word/Excel/PPT → PDF | ✅ |
| OCR 图片转文字 | PaddleOCR / RapidOCR | 🔜 |
| PDF 合并/拆分/压缩 | pypdf | 🔜 |
| AI 翻译/写作/摘要 | OpenAI 兼容接口 | 🔜 |

完整路线图：[docs/roadmap.md](docs/roadmap.md)

## 快速开始

```bash
# 1) 环境（Python ≥3.10）
python3 -m venv .venv
.venv/bin/pip install -e "engine[dev]"

# 2) PDF → Word
.venv/bin/officekit pdf2word demo/report.pdf -o demo/roundtrip.docx
.venv/bin/officekit pdf2word foo.pdf --pages 1-5,8

# 3) Word/Excel/PPT → PDF（需本机安装 LibreOffice）
brew install --cask libreoffice        # macOS
.venv/bin/officekit office2pdf demo/report.docx demo/sales.xlsx -o demo

# 4) 跑测试
.venv/bin/pytest engine/tests -v

# 5) 造演示样例
.venv/bin/python scripts/make_samples.py demo
```

Windows 用户：安装 [LibreOffice](https://www.libreoffice.org/download) 后 `soffice.exe` 会自动从默认路径找到。
国内网络 brew 镜像不稳时，可从 [USTC 镜像](https://mirrors.ustc.edu.cn/tdf/libreoffice/stable/) 手动下载 DMG 安装。

## 桌面端（Tauri 2 · macOS / Windows）

```bash
# 开发迭代（需 Rust：rustup；CLI：npm i -g @tauri-apps/cli）
cd desktop && tauri dev

# 构建安装包（改了引擎代码后先重打 sidecar）
.venv/bin/pyinstaller --onefile --name officekit-engine --paths engine \
  --distpath desktop/src-tauri/binaries --workpath /tmp/officekit-pyi \
  --specpath /tmp/officekit-pyi -y scripts/engine_entry.py
mv desktop/src-tauri/binaries/officekit-engine \
   desktop/src-tauri/binaries/officekit-engine-aarch64-apple-darwin   # macOS arm；Windows 为 -x86_64-pc-windows-msvc.exe
cd desktop && tauri build   # 产物：desktop/src-tauri/target/release/bundle/
```

Windows 安装包由 CI 出（Python sidecar 无法交叉编译）：推送 `v*` 标签或手动触发
`.github/workflows/build.yml`（macOS arm/intel + Windows 三平台矩阵）。

> 注：仅「Office 转 PDF」依赖本机 LibreOffice（应用会自动检测并引导安装），其余功能无此依赖。

## 项目结构

```
AGENTS.md              Agent 协作硬规则（先读这个）
README.md              本文件
LICENSES.md            依赖许可证登记
docs/
  roadmap.md           路线图与状态
  architecture.md      架构说明（含 sidecar 协议与踩坑记录）
  research/            每个功能的调研记录（「先搜后写」规则的产物）
engine/
  pyproject.toml       引擎包定义（officekit-engine）
  officekit/           引擎代码（pdf2word / office2pdf / cli / serve）
  tests/               端到端测试（自造样例，不依赖外部文件）
desktop/
  src-ui/              桌面 UI（React + Arco Design + Vite）
  src-tauri/           Tauri 2 壳层（Rust 命令 + sidecar 编排）
  .cargo/config.toml   crates.io 国内镜像（rsproxy）
scripts/               辅助脚本（样例生成 / sidecar 打包入口 / 图标生成）
assets/icon.png        应用图标源图（工具箱图案）
.github/workflows/     多平台构建 CI
demo/                  演示产物（git 忽略）
```

## 许可证风险提示

pdf2docx（MIT）的底层依赖 **PyMuPDF 为 AGPL-3.0**：内部开发验证无碍，**闭源商用分发前需替换或取得商业授权**。
详见 [LICENSES.md](LICENSES.md)。
