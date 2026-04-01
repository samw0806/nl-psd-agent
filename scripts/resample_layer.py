"""
resample_layer.py — 对已有像素图层进行重建式缩放。

仅支持 pixel 类型图层。本质是"删旧层，造新层"，而非 Photoshop 原生变换。

可能丢失：图层蒙版、clipping 关系、图层效果等高级元数据。

用法:
  python scripts/resample_layer.py <psd_file> "<layer_path>" --scale 0.5
  python scripts/resample_layer.py <psd_file> "<layer_path>" --width 600
  python scripts/resample_layer.py <psd_file> "<layer_path>" --height 400
  python scripts/resample_layer.py <psd_file> "<layer_path>" --fit-contain 800x600
"""
import sys
import argparse
from pathlib import Path
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd


def parse_box(box_str: str) -> tuple[int, int]:
    parts = box_str.lower().split("x")
    if len(parts) != 2:
        print(f"错误：盒子尺寸格式应为 WxH（如 800x600），得到 '{box_str}'", file=sys.stderr)
        sys.exit(1)
    return int(parts[0]), int(parts[1])


def main():
    parser = argparse.ArgumentParser(
        description="像素图层重建式缩放（仅支持 pixel 类型图层）",
        epilog="警告：此操作会删除原图层并重建，可能丢失蒙版、clipping 等高级属性。"
    )
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Body/Product'）")
    size_group = parser.add_mutually_exclusive_group(required=True)
    size_group.add_argument("--scale", type=float, help="缩放比例（如 0.5 表示缩小到 50%%）")
    size_group.add_argument("--width", type=int, help="目标宽度（等比缩放）")
    size_group.add_argument("--height", type=int, help="目标高度（等比缩放）")
    size_group.add_argument("--fit-contain", metavar="WxH", help="完整放进盒子，不裁剪")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, parent = find_layer(psd, args.layer_path)

    # 检查图层类型
    kind = str(layer.kind).lower()
    if "pixel" not in kind:
        print(f"错误：图层 '{args.layer_path}' 类型为 {layer.kind}，不是像素图层", file=sys.stderr)
        print(f"重建式缩放仅支持像素图层（pixel）。文字/形状/智能对象图层不支持。", file=sys.stderr)
        sys.exit(1)

    # 记录原属性
    old_name = layer.name
    old_visible = layer.visible
    old_opacity = layer.opacity
    old_blend = layer.blend_mode
    old_top = layer.top
    old_left = layer.left
    old_w = layer.width
    old_h = layer.height

    # 找到原图层在父容器中的位置
    siblings = list(parent)
    old_idx = siblings.index(layer)

    # 提取图层图像
    try:
        img = layer.topil()
    except Exception:
        try:
            img = layer.composite()
        except Exception as e:
            print(f"错误：无法提取图层图像: {e}", file=sys.stderr)
            sys.exit(1)

    if img is None:
        print(f"错误：图层 '{args.layer_path}' 无法提取图像", file=sys.stderr)
        sys.exit(1)

    original_size = img.size

    # 计算目标尺寸
    w, h = img.size
    if args.scale:
        new_w = round(w * args.scale)
        new_h = round(h * args.scale)
    elif args.width:
        new_w = args.width
        new_h = round(h * new_w / w)
    elif args.height:
        new_h = args.height
        new_w = round(w * new_h / h)
    else:  # fit_contain
        box_w, box_h = parse_box(args.fit_contain)
        ratio = min(box_w / w, box_h / h)
        new_w, new_h = round(w * ratio), round(h * ratio)

    # 重采样
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    resized = img.resize((new_w, new_h), PILImage.LANCZOS)

    # 删除原图层
    parent.remove(layer)

    # 创建新图层（保持原位置）
    try:
        new_layer = psd.create_pixel_layer(resized, name=old_name, top=old_top, left=old_left)
        new_layer.name = old_name  # 确保写入 UNICODE_LAYER_NAME tagged block，避免中文乱码
        new_layer.visible = old_visible
        new_layer.opacity = old_opacity
        new_layer.blend_mode = old_blend
        parent.insert(old_idx, new_layer)
    except Exception as e:
        print(f"错误：创建新图层失败: {e}", file=sys.stderr)
        sys.exit(1)

    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{old_name}' 已完成重建式缩放（警告：这是重建操作，非原生变换）")
    print(f"  原始尺寸: {original_size[0]}×{original_size[1]}")
    print(f"  新尺寸:   {new_w}×{new_h}")
    print(f"  已恢复属性: 名称、位置、可见性、不透明度、混合模式")
    print(f"  可能丢失: 图层蒙版、clipping 关系、图层效果等高级属性")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
