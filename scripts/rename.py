"""
rename.py — 重命名图层。

用法:
  python scripts/rename.py <psd_file> "<layer_path>" "<new_name>"
  python scripts/rename.py <psd_file> "<layer_path>" "<new_name>" --output modified.psd
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def main():
    parser = argparse.ArgumentParser(description="重命名图层")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Header/Logo'）")
    parser.add_argument("new_name", help="新名称")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    old_name = layer.name
    layer.name = args.new_name
    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层已重命名: '{old_name}' → '{args.new_name}'")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
