"""
read_text.py — 读取文字图层的内容和样式信息（只读，不能修改）。

用法:
  python scripts/read_text.py <psd_file> "<layer_path>"
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _utils import open_psd, find_layer


def format_color(color) -> str:
    """将颜色对象格式化为 HEX 或描述字符串。"""
    if color is None:
        return "未知"
    try:
        if hasattr(color, "r"):
            r, g, b = int(color.r), int(color.g), int(color.b)
        elif hasattr(color, "__iter__"):
            vals = list(color)
            if len(vals) >= 3:
                r, g, b = int(vals[0]), int(vals[1]), int(vals[2])
            else:
                return str(color)
        else:
            return str(color)
        return f"#{r:02X}{g:02X}{b:02X} (rgb({r},{g},{b}))"
    except Exception:
        return str(color)


def main():
    parser = argparse.ArgumentParser(description="读取文字图层内容和样式（只读）")
    parser.add_argument("psd_file", help="PSD/PSB 文件路径")
    parser.add_argument("layer_path", help="文字图层路径（如 'Header/Title'）")
    args = parser.parse_args()

    psd = open_psd(args.psd_file)
    layer, _ = find_layer(psd, args.layer_path)

    kind = str(layer.kind).lower()
    if "type" not in kind:
        print(f"错误：图层 '{args.layer_path}' 不是文字图层（类型: {layer.kind}）", file=sys.stderr)
        print(f"提示：文字图层在 info.py 输出中标记为 [Type]", file=sys.stderr)
        sys.exit(1)

    print(f"文字图层: {args.layer_path}")
    print(f"{'─' * 40}")

    # 基本文字内容
    text = getattr(layer, "text", None)
    if text:
        print(f"文字内容: {repr(text)}")
    else:
        print(f"文字内容: (空)")

    # 尝试读取排版细节
    try:
        typesetting = layer.typesetting
        if typesetting is not None:
            print()
            print("排版详情:")
            for p_idx, paragraph in enumerate(typesetting):
                # 对齐方式
                style = getattr(paragraph, "style", None)
                justification = getattr(style, "justification", None) if style else None
                if justification:
                    print(f"  段落 {p_idx + 1} 对齐: {justification}")

                # 文字片段（run）
                for r_idx, run in enumerate(paragraph):
                    run_text = getattr(run, "text", "")
                    run_style = getattr(run, "style", None)
                    if run_style:
                        font = getattr(run_style, "font_name", None)
                        size = getattr(run_style, "font_size", None)
                        color = getattr(run_style, "color", None)
                        bold = getattr(run_style, "bold", None)
                        italic = getattr(run_style, "italic", None)

                        attrs = []
                        if font:
                            attrs.append(f"字体:{font}")
                        if size:
                            attrs.append(f"字号:{size}pt")
                        if color is not None:
                            attrs.append(f"颜色:{format_color(color)}")
                        if bold:
                            attrs.append("粗体")
                        if italic:
                            attrs.append("斜体")

                        print(f"    片段 {r_idx + 1}: {repr(run_text)} | {' | '.join(attrs)}")
    except Exception as e:
        print(f"  (排版细节读取失败: {e})")

    print()
    print("注意：文字内容为只读，psd-tools 不支持修改文字图层内容。")


if __name__ == "__main__":
    main()
