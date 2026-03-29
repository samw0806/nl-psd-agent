"""
公共工具模块：图层路径解析、错误处理等。
所有脚本共用此模块。
"""
import sys
from pathlib import Path
from psd_tools import PSDImage


def open_psd(psd_path: str) -> PSDImage:
    """打开 PSD/PSB 文件，失败时输出错误并退出。"""
    p = Path(psd_path)
    if not p.exists():
        print(f"错误：文件不存在: {psd_path}", file=sys.stderr)
        sys.exit(1)
    if p.suffix.lower() not in (".psd", ".psb"):
        print(f"错误：不支持的文件格式: {p.suffix}（仅支持 .psd / .psb）", file=sys.stderr)
        sys.exit(1)
    try:
        return PSDImage.open(psd_path)
    except Exception as e:
        print(f"错误：无法打开文件 {psd_path}: {e}", file=sys.stderr)
        sys.exit(1)


def save_psd(psd: PSDImage, psd_path: str, output_path: str | None = None) -> str:
    """保存 PSD 文件，返回实际保存路径。"""
    target = output_path or psd_path
    try:
        psd.save(target)
        return target
    except Exception as e:
        print(f"错误：无法保存文件 {target}: {e}", file=sys.stderr)
        sys.exit(1)


def find_layer(psd: PSDImage, layer_path: str):
    """
    按路径查找图层。路径用 "/" 分隔，例如 "Header/Logo"。
    返回 (layer, parent) 元组，找不到时输出错误并退出。
    """
    parts = [p.strip() for p in layer_path.split("/") if p.strip()]
    if not parts:
        print(f"错误：图层路径不能为空", file=sys.stderr)
        sys.exit(1)

    current = psd
    parent = None
    for i, name in enumerate(parts):
        found = None
        for child in current:
            if child.name == name:
                found = child
                break
        if found is None:
            searched_in = "/".join(parts[:i]) if i > 0 else "(根层)"
            print(f"错误：在 '{searched_in}' 中找不到图层 '{name}'", file=sys.stderr)
            print(f"提示：请先运行 python scripts/info.py <文件> 查看完整图层结构", file=sys.stderr)
            sys.exit(1)
        parent = current
        current = found

    return current, parent


def ensure_tmp_dir(psd_path: str) -> Path:
    """确保 .tmp 目录存在，返回其路径。"""
    psd_dir = Path(psd_path).parent
    # 优先在 PSD 文件所在目录的 .tmp，若不存在则用脚本目录的 .tmp
    tmp_dir = psd_dir / ".tmp"
    if not tmp_dir.exists():
        # 尝试项目根目录的 .tmp
        script_dir = Path(__file__).parent.parent
        tmp_dir = script_dir / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def layer_type_label(layer) -> str:
    """返回图层类型的简短标签。"""
    kind = str(layer.kind).lower() if hasattr(layer, "kind") else ""
    if "type" in kind:
        return "Type"
    elif "pixel" in kind:
        return "Pixel"
    elif "group" in kind:
        return "Group"
    elif "shape" in kind:
        return "Shape"
    elif "smartobject" in kind or "smart" in kind:
        return "Smart"
    elif "solidcolorfill" in kind or "fill" in kind:
        return "Fill"
    elif "adjustment" in kind:
        return "Adjust"
    else:
        return "Layer"
