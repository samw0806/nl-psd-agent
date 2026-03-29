"""
reorder.py — 图层排序（上移、下移、移到指定索引）。

用法:
  python scripts/reorder.py <psd_file> "<layer_path>" --up
  python scripts/reorder.py <psd_file> "<layer_path>" --down
  python scripts/reorder.py <psd_file> "<layer_path>" --to-index 0
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="图层排序")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Header/Logo'）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--up", action="store_true", help="上移一层（在图层面板中向上）")
    group.add_argument("--down", action="store_true", help="下移一层（在图层面板中向下）")
    group.add_argument("--to-index", type=int, metavar="N", help="移到指定索引（0 = 最顶层）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, parent = find_layer(psd, args.layer_path)

    siblings = list(parent)
    if layer not in siblings:
        print(f"错误：无法找到图层在父容器中的位置", file=sys.stderr)
        sys.exit(1)

    current_idx = siblings.index(layer)
    total = len(siblings)

    if args.up:
        if current_idx == 0:
            print(f"图层 '{args.layer_path}' 已在最顶层，无法上移")
            return
        # psd-tools 中索引 0 是最顶层，上移 = 索引减小
        parent.remove(layer)
        parent.insert(current_idx - 1, layer)
        action = f"上移 (索引 {current_idx} → {current_idx - 1})"

    elif args.down:
        if current_idx == total - 1:
            print(f"图层 '{args.layer_path}' 已在最底层，无法下移")
            return
        parent.remove(layer)
        parent.insert(current_idx + 1, layer)
        action = f"下移 (索引 {current_idx} → {current_idx + 1})"

    else:  # to_index
        target_idx = args.to_index
        if target_idx < 0 or target_idx >= total:
            print(f"错误：索引 {target_idx} 超出范围（当前共 {total} 个图层，有效范围 0-{total-1}）", file=sys.stderr)
            sys.exit(1)
        parent.remove(layer)
        parent.insert(target_idx, layer)
        action = f"移到索引 {target_idx}"

    saved = save_psd(psd, args.psd_file, args.output)
    print(f"图层 '{args.layer_path}' 已{action}")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
