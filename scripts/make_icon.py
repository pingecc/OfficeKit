"""生成应用图标源图 assets/icon.png（1024×1024 RGBA，蓝底白色工具箱）。

用法：.venv/bin/python scripts/make_icon.py
随后执行：tauri icon assets/icon.png -o desktop/src-tauri/icons
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 1024
BLUE = (22, 93, 255, 255)  # Arco 主色 #165DFF
WHITE = (255, 255, 255, 255)


def main() -> int:
    out = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=200, fill=BLUE)

    # 工具箱：提手（空心圆角框）+ 箱体（实心）+ 扣锁
    draw.rounded_rectangle([352, 258, 672, 480], radius=96, outline=WHITE, width=42)
    draw.rounded_rectangle([192, 430, 832, 776], radius=56, fill=WHITE)
    draw.rounded_rectangle([448, 430, 576, 544], radius=24, fill=BLUE)

    img.save(out)
    print(f"图标已生成：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
