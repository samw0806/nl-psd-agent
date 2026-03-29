"""
opacity.py — 设置图层不透明度。

用法:
  python scripts/opacity.py <psd_file> "<layer_path>" <value>
    value 可以是:
      0-255   整数值
      0%-100% 百分比（如 50%）

示例:
  python scripts/opacity.py banner.psd "Header/Logo" 128
  python scripts/opacity.py banner.psd "Header/Logo" 50%
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def parse_opacity(value: str) -> int:
    """解析不透明度值，支持 0-255 整数或 0%-100% 百分比。"""
    value = value.strip()
    if value.endswith("%"):
        pct = float(value[:-1])
        if not (0 <= pct <= 100):
            print(f"错误：百分比必须在 0-100 之间，得到 {pct}", file=sys.stderr)
            sys.exit(1)
        return round(pct / 100 * 255)
    else:
        v = int(value)
        if not (0 <= v <= 255):
            print(f"错误：不透明度值必须在 0-255 之间，得到 {v}", file=sys.stderr)
            sys.exit(1)
        return v


def main():
    parser = argparse.ArgumentParser(description="设置图层不透明度")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Header/Logo'）")
    parser.add_argument("opacity", help="不透明度值（0-255 或 0%%-100%%）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    new_val = parse_opacity(args.opacity)
    old_val = layer.opacity
    old_pct = int(old_val / 255 * 100)
    new_pct = int(new_val / 255 * 100)

    layer.opacity = new_val
    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{args.layer_path}' 不透明度: {old_val} ({old_pct}%) → {new_val} ({new_pct}%)")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
