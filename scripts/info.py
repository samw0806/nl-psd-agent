"""
info.py — 显示 PSD/PSB 文件信息和图层树。

用法:
  python scripts/info.py <psd_file> [--depth N]
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, layer_type_label


def print_layer_tree(layers, depth: int, max_depth: int, prefix: str = "", is_last: bool = True):
    for i, layer in enumerate(layers):
        is_last_child = (i == len(layers) - 1)
        connector = "└── " if is_last_child else "├── "
        child_prefix = prefix + ("    " if is_last_child else "│   ")

        kind = layer_type_label(layer)
        visible = "可见" if layer.visible else "隐藏"
        opacity_pct = int(layer.opacity / 255 * 100)
        blend = str(layer.blend_mode).replace("BlendMode.", "").lower()

        extra = ""
        if kind == "Type" and hasattr(layer, "text") and layer.text:
            text_preview = layer.text[:20].replace("\n", " ")
            extra = f' | 文字:"{text_preview}"'

        bbox = ""
        if hasattr(layer, "left"):
            bbox = f" | 位置:({layer.left},{layer.top}) 尺寸:{layer.width}×{layer.height}"

        print(f"{prefix}{connector}[{kind}] {layer.name:<20} | {visible} | 不透明度:{opacity_pct}% | {blend}{extra}{bbox}")

        if kind == "Group" and depth < max_depth:
            print_layer_tree(list(layer), depth + 1, max_depth, child_prefix, is_last_child)


def main():
    parser = argparse.ArgumentParser(description="显示 PSD/PSB 文件信息和图层树")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("--depth", type=int, default=10, help="最大显示深度（默认:10）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)

    # 统计图层总数
    total = sum(1 for _ in psd.descendants())

    print(f"文件: {args.psd_file}")
    print(f"尺寸: {psd.width} × {psd.height} px")
    print(f"色彩模式: {psd.color_mode.name}")
    print(f"位深: {psd.depth}")
    print(f"图层数: {total}")
    print()
    print("图层结构:")
    print_layer_tree(list(psd), depth=0, max_depth=args.depth)


if __name__ == "__main__":
    main()
