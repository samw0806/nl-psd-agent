"""
position_layer.py — 调整非组图层的位置。

用法:
  python scripts/position_layer.py <psd_file> "<layer_path>" --dx 40 --dy 20
  python scripts/position_layer.py <psd_file> "<layer_path>" --left 560 --top 108

说明:
  - 相对移动模式：使用 --dx / --dy，未提供的轴默认为 0
  - 绝对定位模式：使用 --left / --top，未提供的轴保持原值
  - 两种模式不能混用
  - 当前仅支持非组图层，组图层请先分别移动其子图层
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd, set_layer_position


def main():
    parser = argparse.ArgumentParser(description="调整非组图层的位置")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Body/ProductShot'）")
    parser.add_argument("--dx", type=int, help="x 方向相对位移（像素，可为负数）")
    parser.add_argument("--dy", type=int, help="y 方向相对位移（像素，可为负数）")
    parser.add_argument("--left", type=int, help="目标 left 坐标（像素）")
    parser.add_argument("--top", type=int, help="目标 top 坐标（像素）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    use_delta = args.dx is not None or args.dy is not None
    use_absolute = args.left is not None or args.top is not None

    if use_delta == use_absolute:
        print("错误：必须且只能选择一种模式：--dx/--dy 或 --left/--top", file=sys.stderr)
        sys.exit(1)

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    if "group" in str(layer.kind).lower():
        print(
            f"错误：图层 '{args.layer_path}' 是组图层，当前仅支持移动非组图层。"
            "请先分别移动组内子图层。",
            file=sys.stderr,
        )
        sys.exit(1)

    old_left = layer.left
    old_top = layer.top

    if use_delta:
        new_left = old_left + (args.dx or 0)
        new_top = old_top + (args.dy or 0)
    else:
        new_left = args.left if args.left is not None else old_left
        new_top = args.top if args.top is not None else old_top

    set_layer_position(layer, new_left, new_top)

    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{args.layer_path}' 已更新位置")
    print(f"  旧位置: left={old_left}, top={old_top}")
    print(f"  新位置: left={new_left}, top={new_top}")
    print(f"  位移量: dx={new_left - old_left}, dy={new_top - old_top}")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
