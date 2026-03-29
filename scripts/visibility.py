"""
visibility.py — 切换图层可见性。

用法:
  python scripts/visibility.py <psd_file> "<layer_path>" --hide
  python scripts/visibility.py <psd_file> "<layer_path>" --show
  python scripts/visibility.py <psd_file> "<layer_path>" --toggle
  python scripts/visibility.py <psd_file> "<layer_path>" --hide --output modified.psd
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="切换图层可见性")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Header/Logo'）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--hide", action="store_true", help="隐藏图层")
    group.add_argument("--show", action="store_true", help="显示图层")
    group.add_argument("--toggle", action="store_true", help="切换可见性")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    before = layer.visible
    if args.hide:
        layer.visible = False
        action = "隐藏"
    elif args.show:
        layer.visible = True
        action = "显示"
    else:  # toggle
        layer.visible = not layer.visible
        action = "显示" if layer.visible else "隐藏"

    after = layer.visible
    if before == after and not args.toggle:
        print(f"图层 '{args.layer_path}' 已经是{'可见' if after else '隐藏'}状态，无需修改")
    else:
        saved = save_psd(psd, args.psd_file, args.output)
        print(f"图层 '{args.layer_path}' 已{action}")
        print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
