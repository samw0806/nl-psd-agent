"""
export.py — 将 PSD 合成导出为 PNG 或 JPG。

用法:
  python scripts/export.py <psd_file> <output_path>
  python scripts/export.py <psd_file> output.jpg --quality 90
  python scripts/export.py <psd_file> output.png --max-size 1920
"""
import sys
import argparse
from pathlib import Path
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd


def main():
    parser = argparse.ArgumentParser(description="将 PSD 合成导出为 PNG/JPG")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("output", help="输出路径（.png 或 .jpg/.jpeg）")
    parser.add_argument("--quality", type=int, default=90, help="JPG 质量（1-95，默认 90）")
    parser.add_argument("--max-size", type=int, help="输出最大边长（可选）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)

    try:
        image = psd.composite()
    except Exception as e:
        print(f"错误：合成失败: {e}", file=sys.stderr)
        sys.exit(1)

    if args.max_size:
        w, h = image.size
        if w > args.max_size or h > args.max_size:
            ratio = min(args.max_size / w, args.max_size / h)
            image = image.resize((round(w * ratio), round(h * ratio)), PILImage.LANCZOS)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = out_path.suffix.lower()

    if suffix in (".jpg", ".jpeg"):
        if image.mode in ("RGBA", "LA", "P"):
            # JPG 不支持透明，转为白底 RGB
            bg = PILImage.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                bg.paste(image, mask=image.split()[3])
            else:
                bg.paste(image.convert("RGB"))
            image = bg
        image.save(str(out_path), "JPEG", quality=args.quality)
    else:
        if image.mode not in ("RGB", "RGBA", "L", "LA"):
            image = image.convert("RGBA")
        image.save(str(out_path), "PNG")

    print(f"已导出: {out_path} ({image.size[0]}×{image.size[1]})")


if __name__ == "__main__":
    main()
