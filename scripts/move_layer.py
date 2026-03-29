"""
move_layer.py — 将图层移动到另一个组。

用法:
  python scripts/move_layer.py <psd_file> "<layer_path>" --to-group "<group_path>"
  python scripts/move_layer.py <psd_file> "<layer_path>" --to-root   # 移到根层
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="将图层移动到另一个组")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="要移动的图层路径（如 'Header/Logo'）")
    dest = parser.add_mutually_exclusive_group(required=True)
    dest.add_argument("--to-group", metavar="GROUP_PATH", help="目标组路径（如 'Body'）")
    dest.add_argument("--to-root", action="store_true", help="移到根层（顶层）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, parent = find_layer(psd, args.layer_path)

    # 从原父容器移除
    parent.remove(layer)

    # 插入目标
    if args.to_root:
        psd.append(layer)
        dest_name = "根层"
    else:
        target_group, _ = find_layer(psd, args.to_group)
        if not hasattr(target_group, "append"):
            print(f"错误：'{args.to_group}' 不是图层组，无法移入", file=sys.stderr)
            sys.exit(1)
        target_group.append(layer)
        dest_name = args.to_group

    saved = save_psd(psd, args.psd_file, args.output)
    print(f"图层 '{args.layer_path}' 已移动到 '{dest_name}'")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
