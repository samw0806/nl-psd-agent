"""
rasterize_layer.py — 将 Smart Object / Shape / Type 图层栅格化为像素图层。

⚠️ 不可逆操作：原图层的矢量/文字/智能对象编辑性将永久丢失。

可选同时指定缩放策略（不填则保持原尺寸）：
  --scale 0.8
  --width N
  --height N
  --fit-contain WxH

用法:
  python scripts/rasterize_layer.py <psd_file> "<layer_path>"
  python scripts/rasterize_layer.py <psd_file> "<layer_path>" --scale 0.5
  python scripts/rasterize_layer.py <psd_file> "<layer_path>" --width 600
  python scripts/rasterize_layer.py <psd_file> "<layer_path>" --fit-contain 800x600
"""
import sys
import argparse
from pathlib import Path
from PIL import Image as PILImage

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, layer_type_label, save_psd


def parse_box(box_str: str) -> tuple[int, int]:
    parts = box_str.lower().split("x")
    if len(parts) != 2:
        print(f"错误：盒子尺寸格式应为 WxH（如 800x600），得到 '{box_str}'", file=sys.stderr)
        sys.exit(1)
    return int(parts[0]), int(parts[1])


def main():
    parser = argparse.ArgumentParser(
        description="将 Smart Object / Shape / Type 图层栅格化为像素图层（不可逆）",
        epilog="警告：此操作不可逆，原图层的矢量/文字/智能对象编辑性将永久丢失。"
    )
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="图层路径（如 'Body/SmartObj'）")
    size_group = parser.add_mutually_exclusive_group(required=False)
    size_group.add_argument("--scale", type=float, help="缩放比例（如 0.5 表示缩小到 50%%）")
    size_group.add_argument("--width", type=int, help="目标宽度（等比缩放）")
    size_group.add_argument("--height", type=int, help="目标高度（等比缩放）")
    size_group.add_argument("--fit-contain", metavar="WxH", help="完整放进盒子，不裁剪")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, parent = find_layer(psd, args.layer_path)

    # 检查图层类型
    kind = layer_type_label(layer)
    if kind == "Pixel":
        print(f"图层 '{args.layer_path}' 已经是像素图层，无需栅格化。", file=sys.stderr)
        print(f"如需缩放，请直接使用 resample_layer.py。", file=sys.stderr)
        sys.exit(0)
    if kind == "Group":
        print(f"错误：图层 '{args.layer_path}' 是图层组，不支持栅格化。", file=sys.stderr)
        sys.exit(1)

    # 记录原属性
    old_name = layer.name
    old_visible = layer.visible
    old_opacity = layer.opacity
    old_blend = layer.blend_mode
    old_top = layer.top
    old_left = layer.left

    # 找到原图层在父容器中的位置
    siblings = list(parent)
    old_idx = siblings.index(layer)

    # 提取渲染像素（在删除图层之前先验证）
    img = None
    try:
        img = layer.composite(color=0.0, alpha=0.0, force=True)
    except Exception:
        try:
            img = layer.topil()
        except Exception as e:
            print(f"错误：无法提取图层图像: {e}", file=sys.stderr)
            print(f"提示：此图层可能包含不支持的内容，建议在 Photoshop 中手动处理", file=sys.stderr)
            sys.exit(1)

    if img is None or img.size[0] == 0 or img.size[1] == 0:
        print(f"错误：图层 '{args.layer_path}' 无法提取有效图像（可能是空图层）", file=sys.stderr)
        sys.exit(1)

    original_size = img.size

    # 计算目标尺寸并预先处理图像（在删除图层之前）
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
    elif args.fit_contain:
        box_w, box_h = parse_box(args.fit_contain)
        ratio = min(box_w / w, box_h / h)
        new_w, new_h = round(w * ratio), round(h * ratio)
    else:
        new_w, new_h = w, h

    # 预先处理图像（转换格式、缩放）
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if (new_w, new_h) != (w, h):
        img = img.resize((new_w, new_h), PILImage.LANCZOS)

    # 现在才删除原图层并创建新图层
    parent.remove(layer)

    # 创建新像素图层（保持原位置）
    try:
        new_layer = psd.create_pixel_layer(img, name=old_name, top=old_top, left=old_left)
        new_layer.name = old_name  # 确保写入 UNICODE_LAYER_NAME tagged block，避免中文乱码
        new_layer.visible = old_visible
        new_layer.opacity = old_opacity
        new_layer.blend_mode = old_blend
        parent.insert(old_idx, new_layer)
    except Exception as e:
        print(f"错误：创建像素图层失败: {e}", file=sys.stderr)
        sys.exit(1)

    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{old_name}' 已栅格化（{kind} → Pixel）⚠️ 此操作不可逆")
    print(f"  原始尺寸: {original_size[0]}×{original_size[1]}")
    print(f"  像素尺寸: {new_w}×{new_h}")
    print(f"  已恢复属性: 名称、位置、可见性、不透明度、混合模式")
    print(f"  丢失属性: 矢量/文字/智能对象编辑性、图层蒙版、clipping 关系、图层效果")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
