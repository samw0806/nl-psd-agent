"""
extract_smart_object.py — 提取智能对象图层中的嵌入文件。

用法:
  python scripts/extract_smart_object.py <psd_file> "<layer_path>"
  python scripts/extract_smart_object.py <psd_file> "<layer_path>" --output extracted.png
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer


def main():
    parser = argparse.ArgumentParser(description="提取智能对象中的嵌入文件")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="智能对象图层路径（如 'Body/Product'）")
    parser.add_argument("--output", help="输出文件路径（默认根据嵌入类型自动命名）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    kind = str(layer.kind).lower()
    if "smartobject" not in kind and "smart" not in kind:
        print(f"错误：图层 '{args.layer_path}' 不是智能对象（类型: {layer.kind}）", file=sys.stderr)
        sys.exit(1)

    # 获取智能对象数据
    smart = getattr(layer, "smart_object", None)
    if smart is None:
        print(f"错误：无法获取图层 '{args.layer_path}' 的智能对象数据", file=sys.stderr)
        sys.exit(1)

    data = getattr(smart, "data", None)
    if data is None:
        print(f"错误：智能对象中没有嵌入数据", file=sys.stderr)
        sys.exit(1)

    # 确定扩展名
    filename = getattr(smart, "filename", None) or layer.name
    kind_ext = getattr(smart, "kind", "bin")

    if args.output:
        out_path = Path(args.output)
    else:
        stem = Path(filename).stem if filename else layer.name
        ext = Path(filename).suffix if (filename and Path(filename).suffix) else f".{kind_ext}"
        out_path = Path(f"{stem}_extracted{ext}")

    out_path.write_bytes(data)
    print(f"已提取智能对象内容")
    print(f"  图层: {args.layer_path}")
    print(f"  文件大小: {len(data)} 字节")
    print(f"  保存到: {out_path}")


if __name__ == "__main__":
    main()
