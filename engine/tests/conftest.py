import pytest

from officekit.office2pdf import find_soffice


@pytest.fixture(scope="session")
def soffice() -> str:
    """LibreOffice 可执行文件路径；未安装则跳过 office2pdf 端到端测试。"""
    path = find_soffice()
    if not path:
        pytest.skip(
            "未安装 LibreOffice，跳过 office2pdf 端到端测试"
            "（安装：brew install --cask libreoffice）"
        )
    return path
