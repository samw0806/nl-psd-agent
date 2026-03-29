"""
export_layers.py — 批量导出所有图层各自的 PNG。

用法:
  python scripts/export_layers.py <psd_file>
  python scripts/export_layers.py <psd_file> --output-dir ./layers/
  python scripts/export_layers.py <psd_file> --visible-only  # 只导出可见图层
"""
import sys
import argparse
import re
from pathlib import Path
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, layer_type_label


def safe_filename(name: str) -> str:
    """将图层名转为合法文件名。"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def export_layer(layer, out_dir: Path, prefix: str, visible_only: bool, count: list):
    label = layer_type_label(layer)
    is_group = label == "Group"

    if visible_only and not layer.visible:
        return

    if not is_group:
        try:
            img = layer.composite()
            if img is not None:
                if img.mode not in ("RGB", "RGBA", "L", "LA"):
                    img = img.convert("RGBA")
                fname = f"{prefix}{safe_filename(layer.name)}.png"
                img.save(str(out_dir / fname))
                count[0] += 1
                print(f"  导出: {fname} ({img.size[0]}×{img.size[1]})")
        except Exception as e:
            print(f"  跳过 '{layer.name}': {e}")

    if is_group:
        new_prefix = f"{prefix}{safe_filename(layer.name)}_"
        for child in layer:
            export_layer(child, out_dir, new_prefix, visible_only, count)


def main():
    parser = argparse.ArgumentParser(description="批量导出所有图层为独立 PNG")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("--output-dir", default="./layers", help="输出目录（默认 ./layers/）")
    parser.add_argument("--visible-only", action="store_true", help="只导出可见图层")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = [0]
    print(f"开始导出图层到 {out_dir}/")
    for layer in psd:
        export_layer(layer, out_dir, "", args.visible_only, count)

    print(f"\n共导出 {count[0]} 个图层到 {out_dir}/")


if __name__ == "__main__":
    main()
