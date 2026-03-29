"""
create_group.py — 创建图层组，可选将现有图层归入。

用法:
  python scripts/create_group.py <psd_file> "<group_name>"
  python scripts/create_group.py <psd_file> "<group_name>" --layers "Layer1,Layer2,Layer3"
  python scripts/create_group.py <psd_file> "<group_name>" --parent "Header"
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="创建图层组")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("group_name", help="新组的名称")
    parser.add_argument("--layers", help="要归入组的图层名列表，逗号分隔（如 'Logo,Title,Subtitle'）")
    parser.add_argument("--parent", help="在哪个组内创建（默认在根层）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)

    # 确定父容器
    if args.parent:
        parent_layer, _ = find_layer(psd, args.parent)
        container = parent_layer
    else:
        container = psd

    # 收集要移入的图层
    layers_to_move = []
    if args.layers:
        names = [n.strip() for n in args.layers.split(",") if n.strip()]
        for name in names:
            found = None
            for child in container:
                if child.name == name:
                    found = child
                    break
            if found is None:
                print(f"错误：在 '{args.parent or '根层'}' 中找不到图层 '{name}'", file=sys.stderr)
                sys.exit(1)
            layers_to_move.append(found)

    # 创建组
    try:
        if layers_to_move:
            new_group = psd.create_group(name=args.group_name, layer_list=layers_to_move)
        else:
            new_group = psd.create_group(name=args.group_name)
        container.append(new_group)
    except Exception as e:
        print(f"错误：创建组失败: {e}", file=sys.stderr)
        sys.exit(1)

    saved = save_psd(psd, args.psd_file, args.output)

    print(f"已创建图层组 '{args.group_name}'")
    if layers_to_move:
        print(f"  已将以下图层归入组: {', '.join(l.name for l in layers_to_move)}")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
