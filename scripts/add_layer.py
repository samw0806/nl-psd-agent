"""
add_layer.py — 从外部图片添加新像素图层，支持插入前缩放。

用法:
  python scripts/add_layer.py <psd_file> <image_file> [选项]

尺寸策略（每次只能选一种）:
  --width N           按目标宽度等比缩放
  --height N          按目标高度等比缩放
  --scale 0.5         按比例缩放（0.1~10.0）
  --fit-contain WxH   完整放进盒子，不裁剪（如 800x800）
  --fit-cover WxH     铺满盒子，必要时裁剪（如 800x800）

位置选项:
  --top N             图层顶部 y 坐标（默认 0）
  --left N            图层左部 x 坐标（默认 0）
  --center            自动居中放置（覆盖 --top/--left）

其他:
  --name "图层名"     图层名称（默认使用图片文件名）
  --group "组路径"    插入到指定组（如 "Header"）
  --output 路径       另存为路径（默认覆盖原文件）

示例:
  python scripts/add_layer.py banner.psd product.png --name "Product" --width 600 --center
  python scripts/add_layer.py banner.psd logo.png --name "Logo" --fit-contain 400x200 --center
  python scripts/add_layer.py banner.psd bg.jpg --name "Background" --scale 0.5 --top 0 --left 0
"""
import sys
import argparse
from pathlib import Path
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def parse_box(box_str: str) -> tuple[int, int]:
    """解析 WxH 格式，返回 (width, height)。"""
    parts = box_str.lower().replace("x", "x").split("x")
    if len(parts) != 2:
        print(f"错误：盒子尺寸格式应为 WxH（如 800x600），得到 '{box_str}'", file=sys.stderr)
        sys.exit(1)
    return int(parts[0]), int(parts[1])


def apply_size_strategy(img: PILImage.Image, args) -> PILImage.Image:
    """根据参数应用尺寸策略，返回调整后的图片。"""
    w, h = img.size

    if args.width:
        new_w = args.width
        new_h = round(h * new_w / w)
        return img.resize((new_w, new_h), PILImage.LANCZOS)

    elif args.height:
        new_h = args.height
        new_w = round(w * new_h / h)
        return img.resize((new_w, new_h), PILImage.LANCZOS)

    elif args.scale:
        new_w = round(w * args.scale)
        new_h = round(h * args.scale)
        return img.resize((new_w, new_h), PILImage.LANCZOS)

    elif args.fit_contain:
        box_w, box_h = parse_box(args.fit_contain)
        ratio = min(box_w / w, box_h / h)
        new_w, new_h = round(w * ratio), round(h * ratio)
        return img.resize((new_w, new_h), PILImage.LANCZOS)

    elif args.fit_cover:
        box_w, box_h = parse_box(args.fit_cover)
        ratio = max(box_w / w, box_h / h)
        new_w, new_h = round(w * ratio), round(h * ratio)
        resized = img.resize((new_w, new_h), PILImage.LANCZOS)
        # 居中裁剪
        left = (new_w - box_w) // 2
        top = (new_h - box_h) // 2
        return resized.crop((left, top, left + box_w, top + box_h))

    return img  # 不指定尺寸策略则保持原始尺寸


def main():
    parser = argparse.ArgumentParser(description="从外部图片添加新像素图层（支持插入前缩放）")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("image_file", help="要插入的图片路径")

    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument("--width", type=int, help="目标宽度（等比缩放）")
    size_group.add_argument("--height", type=int, help="目标高度（等比缩放）")
    size_group.add_argument("--scale", type=float, help="缩放比例（如 0.5 表示 50%%）")
    size_group.add_argument("--fit-contain", metavar="WxH", help="完整放进盒子，不裁剪")
    size_group.add_argument("--fit-cover", metavar="WxH", help="铺满盒子，必要时裁剪")

    parser.add_argument("--top", type=int, default=0, help="图层顶部 y 坐标（默认 0）")
    parser.add_argument("--left", type=int, default=0, help="图层左部 x 坐标（默认 0）")
    parser.add_argument("--center", action="store_true", help="自动居中放置")
    parser.add_argument("--name", help="图层名称（默认使用图片文件名）")
    parser.add_argument("--group", help="插入到指定组（如 'Header'）")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    # 打开图片
    img_path = Path(args.image_file)
    if not img_path.exists():
        print(f"错误：图片文件不存在: {args.image_file}", file=sys.stderr)
        sys.exit(1)

    try:
        img = PILImage.open(str(img_path))
    except Exception as e:
        print(f"错误：无法打开图片 {args.image_file}: {e}", file=sys.stderr)
        sys.exit(1)

    original_size = img.size

    # 转为 RGBA
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # 应用尺寸策略
    img = apply_size_strategy(img, args)
    final_size = img.size

    # 打开 PSD
    psd = open_psd(args.psd_file)

    # 计算位置
    top = args.top
    left = args.left
    if args.center:
        left = (psd.width - final_size[0]) // 2
        top = (psd.height - final_size[1]) // 2

    # 确定图层名
    layer_name = args.name or img_path.stem

    # 确定插入目标（组或根）
    if args.group:
        target, _ = find_layer(psd, args.group)
        kind = layer_type_label_str(target)
        if "Group" not in str(type(target).__name__) and not hasattr(target, "__iter__"):
            print(f"错误：'{args.group}' 不是图层组", file=sys.stderr)
            sys.exit(1)
    else:
        target = psd

    # 创建像素图层
    try:
        new_layer = psd.create_pixel_layer(img, name=layer_name, top=top, left=left)
        target.append(new_layer)
    except Exception as e:
        print(f"错误：创建图层失败: {e}", file=sys.stderr)
        sys.exit(1)

    saved = save_psd(psd, args.psd_file, args.output)

    print(f"已添加图层 '{layer_name}'")
    print(f"  原始尺寸: {original_size[0]}×{original_size[1]}")
    print(f"  最终尺寸: {final_size[0]}×{final_size[1]}")
    print(f"  位置: top={top}, left={left}")
    if args.group:
        print(f"  已插入到组: {args.group}")
    print(f"文件已保存到 {saved}")


def layer_type_label_str(layer) -> str:
    return type(layer).__name__


if __name__ == "__main__":
    main()
