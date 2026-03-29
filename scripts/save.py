"""
save.py — 保存 PSD 文件（另存为）。

用法:
  python scripts/save.py <psd_file>                    # 覆盖保存原文件
  python scripts/save.py <psd_file> --output new.psd   # 另存为新文件
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, save_psd


def main():
    parser = argparse.ArgumentParser(description="保存 PSD 文件")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("--output", help="另存为路径（不指定则覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    saved = save_psd(psd, args.psd_file, args.output)
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
