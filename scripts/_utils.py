"""
公共工具模块：图层路径解析、错误处理等。
所有脚本共用此模块。
"""
import sys
import os

# 强制设置 UTF-8 编码（必须在导入 psd_tools 之前）
os.environ['LANG'] = 'C.UTF-8'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from pathlib import Path

# Monkey patch psd-tools 的编码问题（必须在导入任何 psd_tools 模块之前）
import psd_tools.psd.bin_utils as bin_utils

_original_write_pascal_string = bin_utils.write_pascal_string

def _patched_write_pascal_string(fp, value, encoding="macroman", padding=2):
    """修复 psd-tools 的编码问题：使用 UTF-8 而不是 macroman"""
    # 尝试使用 UTF-8
    try:
        data = value.encode("utf-8")
        written = bin_utils.write_fmt(fp, "B", len(data))
        written += bin_utils.write_bytes(fp, data)
        written += bin_utils.write_padding(fp, written, padding)
        return written
    except Exception:
        # 回退到 ASCII + 替换不支持的字符
        try:
            data = value.encode("ascii", errors="replace")
            written = bin_utils.write_fmt(fp, "B", len(data))
            written += bin_utils.write_bytes(fp, data)
            written += bin_utils.write_padding(fp, written, padding)
            return written
        except Exception:
            # 最后回退到原始实现
            return _original_write_pascal_string(fp, value, encoding, padding)

# 应用 patch 到 bin_utils 模块
bin_utils.write_pascal_string = _patched_write_pascal_string

# 同时 patch 所有已经导入 write_pascal_string 的模块
import psd_tools.psd.layer_and_mask
psd_tools.psd.layer_and_mask.write_pascal_string = _patched_write_pascal_string

import psd_tools.psd.image_resources
psd_tools.psd.image_resources.write_pascal_string = _patched_write_pascal_string

import psd_tools.psd.linked_layer
psd_tools.psd.linked_layer.write_pascal_string = _patched_write_pascal_string

import psd_tools.psd.patterns
psd_tools.psd.patterns.write_pascal_string = _patched_write_pascal_string

import psd_tools.psd.tagged_blocks
psd_tools.psd.tagged_blocks.write_pascal_string = _patched_write_pascal_string

import psd_tools.psd.filter_effects
psd_tools.psd.filter_effects.write_pascal_string = _patched_write_pascal_string

# 现在才导入 PSDImage
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
    """保存 PSD 文件，返回实际保存路径。使用临时文件 + 原子替换确保安全。"""
    import shutil
    import traceback

    target = output_path or psd_path
    temp_path = Path(target).with_suffix('.psd.tmp')

    try:
        # 先保存到临时文件
        psd.save(str(temp_path))

        # 验证临时文件可读
        try:
            PSDImage.open(str(temp_path))
        except Exception as e:
            print(f"错误：保存的文件无法读取: {e}", file=sys.stderr)
            if temp_path.exists():
                temp_path.unlink()
            sys.exit(1)

        # 原子性替换
        shutil.move(str(temp_path), target)
        return target

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"错误：无法保存文件 {target}: {e}", file=sys.stderr)
        traceback.print_exc()  # 打印完整堆栈跟踪
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
