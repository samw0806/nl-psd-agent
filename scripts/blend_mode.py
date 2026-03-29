"""
blend_mode.py — 设置图层混合模式。

用法:
  python scripts/blend_mode.py <psd_file> "<layer_path>" <mode>
  python scripts/blend_mode.py --list    # 列出所有支持的混合模式

示例:
  python scripts/blend_mode.py banner.psd "Header/Logo" multiply
  python scripts/blend_mode.py banner.psd "Header/Logo" screen
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer, save_psd

try:
    from psd_tools.constants import BlendMode
except ImportError:
    from psd_tools.api.psd_image import BlendMode

# 用户友好名称 → BlendMode 枚举
BLEND_MODE_MAP = {
    "normal": BlendMode.NORMAL,
    "dissolve": BlendMode.DISSOLVE,
    "darken": BlendMode.DARKEN,
    "multiply": BlendMode.MULTIPLY,
    "color_burn": BlendMode.COLOR_BURN,
    "linear_burn": BlendMode.LINEAR_BURN,
    "darker_color": BlendMode.DARKER_COLOR,
    "lighten": BlendMode.LIGHTEN,
    "screen": BlendMode.SCREEN,
    "color_dodge": BlendMode.COLOR_DODGE,
    "linear_dodge": BlendMode.LINEAR_DODGE,
    "lighter_color": BlendMode.LIGHTER_COLOR,
    "overlay": BlendMode.OVERLAY,
    "soft_light": BlendMode.SOFT_LIGHT,
    "hard_light": BlendMode.HARD_LIGHT,
    "vivid_light": BlendMode.VIVID_LIGHT,
    "linear_light": BlendMode.LINEAR_LIGHT,
    "pin_light": BlendMode.PIN_LIGHT,
    "hard_mix": BlendMode.HARD_MIX,
    "difference": BlendMode.DIFFERENCE,
    "exclusion": BlendMode.EXCLUSION,
    "subtract": BlendMode.SUBTRACT,
    "divide": BlendMode.DIVIDE,
    "hue": BlendMode.HUE,
    "saturation": BlendMode.SATURATION,
    "color": BlendMode.COLOR,
    "luminosity": BlendMode.LUMINOSITY,
}


def main():
    parser = argparse.ArgumentParser(description="设置图层混合模式")
    parser.add_argument("psd_file", nargs="?", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", nargs="?", help="图层路径（如 'Header/Logo'）")
    parser.add_argument("mode", nargs="?", help="混合模式名称")
    parser.add_argument("--list", action="store_true", help="列出所有支持的混合模式")
    parser.add_argument("--output", help="另存为路径（默认覆盖原文件）")
    args = parser.parse_args()

    if args.list:
        print("支持的混合模式:")
        for name in BLEND_MODE_MAP:
            print(f"  {name}")
        return

    if not args.psd_file or not args.layer_path or not args.mode:
        parser.print_help()
        sys.exit(1)

    mode_key = args.mode.lower().replace(" ", "_").replace("-", "_")
    if mode_key not in BLEND_MODE_MAP:
        print(f"错误：不支持的混合模式 '{args.mode}'", file=sys.stderr)
        print(f"运行 python scripts/blend_mode.py --list 查看所有支持的模式", file=sys.stderr)
        sys.exit(1)

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    old_mode = str(layer.blend_mode).replace("BlendMode.", "").lower()
    layer.blend_mode = BLEND_MODE_MAP[mode_key]
    saved = save_psd(psd, args.psd_file, args.output)

    print(f"图层 '{args.layer_path}' 混合模式: {old_mode} → {mode_key}")
    print(f"文件已保存到 {saved}")


if __name__ == "__main__":
    main()
