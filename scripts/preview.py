"""
preview.py — 合成预览图并保存到 .tmp/ 目录。

用法:
  python scripts/preview.py <psd_file>                        # 合成整个文档
  python scripts/preview.py <psd_file> --layer "Header/Logo" # 合成指定图层
  python scripts/preview.py <psd_file> --max-size 1024       # 限制输出尺寸（默认 1024）
  python scripts/preview.py <psd_file> --full-size           # 输出原始尺寸
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, ensure_tmp_dir


def main():
    parser = argparse.ArgumentParser(description="生成 PSD 合成预览图")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("--layer", help="指定图层路径（如 'Header/Logo'），不指定则合成整个文档")
    parser.add_argument("--max-size", type=int, default=1024, help="输出图片最大边长（默认 1024px）")
    parser.add_argument("--full-size", action="store_true", help="输出原始尺寸，忽略 --max-size")
    parser.add_argument("--output", help="输出路径（默认 .tmp/preview.png）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)

    if args.layer:
        layer, _ = find_layer(psd, args.layer)
        try:
            image = layer.composite()
        except Exception as e:
            print(f"错误：合成图层 '{args.layer}' 失败: {e}", file=sys.stderr)
            sys.exit(1)
        if image is None:
            print(f"错误：图层 '{args.layer}' 无法合成（可能是空图层）", file=sys.stderr)
            sys.exit(1)
        label = args.layer.replace("/", "_")
        default_name = f"{label}.png"
    else:
        try:
            image = psd.composite()
        except Exception as e:
            print(f"错误：合成文档失败: {e}", file=sys.stderr)
            sys.exit(1)
        default_name = "preview.png"

    original_size = image.size

    # 缩放到 max_size
    if not args.full_size:
        max_side = args.max_size
        w, h = image.size
        if w > max_side or h > max_side:
            ratio = min(max_side / w, max_side / h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            from PIL import Image as PILImage
            image = image.resize((new_w, new_h), PILImage.LANCZOS)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        tmp_dir = ensure_tmp_dir(args.psd_file)
        out_path = tmp_dir / default_name

    # 转为 RGBA 再保存，避免模式不兼容
    if image.mode not in ("RGB", "RGBA", "L", "LA"):
        image = image.convert("RGBA")

    image.save(str(out_path))
    print(f"预览已保存到 {out_path} (原始:{original_size[0]}×{original_size[1]}, 输出:{image.size[0]}×{image.size[1]})")


if __name__ == "__main__":
    main()
