"""
remove_layer.py — 删除图层。

用法:
  python scripts/remove_layer.py <psd_file> "<layer_path>"
  python scripts/remove_layer.py <psd_file> "<layer_path>" --output modified.psd

注意：此操作不可撤销，建议操作前备份原文件。
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="删除图层（不可撤销）")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Header/Logo'）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, parent = find_layer(psd, args.layer_path)

    layer_name = layer.name
    parent.remove(layer)
    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{layer_name}' 已删除")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
