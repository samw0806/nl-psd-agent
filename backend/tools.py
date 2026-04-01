"""
tools.py — 将 scripts/ 中的脚本包装为 Claude Tool 定义和执行函数
"""
import subprocess
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"


def _python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def run_script(script_name: str, args: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """运行 scripts/ 下的脚本，返回 (stdout, stderr, returncode)"""
    import os
    cmd = [_python(), str(SCRIPTS_DIR / script_name)] + args

    # 设置环境变量强制 UTF-8，修复 psd-tools 的编码问题
    env = os.environ.copy()
    env['LANG'] = 'C.UTF-8'
    env['LC_ALL'] = 'C.UTF-8'
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"脚本执行超时: {script_name}, 参数: {args}")
        return "", f"脚本执行超时（{timeout}秒）", 1
    except Exception as e:
        logger.error(f"脚本执行异常: {script_name}, 错误: {str(e)}", exc_info=True)
        return "", f"脚本执行失败: {str(e)}", 1


# ────────────────── Claude Tool 定义 ──────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_psd_info",
        "description": "获取 PSD 文件信息和图层树。打开文件时必须先调用此工具确认图层路径。",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"}
            },
            "required": ["psd_path"]
        }
    },
    {
        "name": "preview_psd",
        "description": "合成 PSD 预览图，保存为 preview.png。每次修改后必须调用以刷新预览。",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer": {"type": "string", "description": "指定图层路径（可选，不填则合成整个文档）"},
                "max_size": {"type": "integer", "description": "输出图片最大边长（默认 1024）"}
            },
            "required": ["psd_path"]
        }
    },
    {
        "name": "set_visibility",
        "description": "显示或隐藏图层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "action": {"type": "string", "enum": ["hide", "show", "toggle"], "description": "操作类型"}
            },
            "required": ["psd_path", "layer_path", "action"]
        }
    },
    {
        "name": "set_opacity",
        "description": "设置图层不透明度",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "value": {"type": "string", "description": "不透明度值，0-255 的整数或百分比如 '50%'"}
            },
            "required": ["psd_path", "layer_path", "value"]
        }
    },
    {
        "name": "set_blend_mode",
        "description": "设置图层混合模式",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "mode": {"type": "string", "description": "混合模式名称，如 normal, multiply, screen, overlay 等"}
            },
            "required": ["psd_path", "layer_path", "mode"]
        }
    },
    {
        "name": "rename_layer",
        "description": "重命名图层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "new_name": {"type": "string", "description": "新名称"}
            },
            "required": ["psd_path", "layer_path", "new_name"]
        }
    },
    {
        "name": "reorder_layer",
        "description": "在同级内上移或下移图层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "direction": {"type": "string", "enum": ["up", "down"], "description": "移动方向"},
                "to_index": {"type": "integer", "description": "移动到指定索引（可选，优先级高于 direction）"}
            },
            "required": ["psd_path", "layer_path", "direction"]
        }
    },
    {
        "name": "move_layer",
        "description": "将图层移动到指定组或移到顶层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "to_group": {"type": "string", "description": "目标组路径（与 to_root 二选一）"},
                "to_root": {"type": "boolean", "description": "是否移到顶层（与 to_group 二选一）"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
    {
        "name": "set_layer_position",
        "description": "调整非组图层的位置。支持相对移动（dx/dy）或绝对坐标（left/top），两种模式不能混用。",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "dx": {"type": "integer", "description": "x 方向相对位移（像素）"},
                "dy": {"type": "integer", "description": "y 方向相对位移（像素）"},
                "left": {"type": "integer", "description": "目标 left 坐标（像素）"},
                "top": {"type": "integer", "description": "目标 top 坐标（像素）"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
    {
        "name": "remove_layer",
        "description": "删除图层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
    {
        "name": "add_layer",
        "description": "从外部图片插入新像素图层",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "image_path": {"type": "string", "description": "要插入的图片路径"},
                "name": {"type": "string", "description": "新图层名称"},
                "width": {"type": "integer", "description": "按宽度等比缩放（像素）"},
                "height": {"type": "integer", "description": "按高度等比缩放（像素）"},
                "scale": {"type": "number", "description": "按比例缩放，如 0.5"},
                "fit_contain": {"type": "string", "description": "完整放进盒子，格式 '800x600'"},
                "fit_cover": {"type": "string", "description": "铺满盒子，格式 '800x600'"},
                "center": {"type": "boolean", "description": "是否居中"}
            },
            "required": ["psd_path", "image_path"]
        }
    },
    {
        "name": "resample_layer",
        "description": "重建式缩放像素图层（仅支持 Pixel 类型图层，会丢失部分属性）",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "scale": {"type": "number", "description": "比例缩放"},
                "width": {"type": "integer", "description": "目标宽度"},
                "height": {"type": "integer", "description": "目标高度"},
                "fit_contain": {"type": "string", "description": "格式 '800x600'"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
    {
        "name": "create_group",
        "description": "创建图层组",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "group_name": {"type": "string", "description": "组名称"},
                "layers": {"type": "string", "description": "要放入组的图层路径，逗号分隔（可选）"}
            },
            "required": ["psd_path", "group_name"]
        }
    },
    {
        "name": "export_psd",
        "description": "将 PSD 导出为 PNG 或 JPG 文件",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "output_path": {"type": "string", "description": "输出路径，.png 或 .jpg"},
                "quality": {"type": "integer", "description": "JPG 质量 1-95（默认 90）"},
                "max_size": {"type": "integer", "description": "最大边长（可选）"}
            },
            "required": ["psd_path", "output_path"]
        }
    },
    {
        "name": "read_text",
        "description": "读取文字图层内容、字体、字号、颜色（只读）",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
    {
        "name": "rasterize_layer",
        "description": "将 Smart Object / Shape / Type 图层栅格化为像素图层（不可逆，会丢失矢量/文字编辑性）。栅格化后可用 resample_layer 缩放。执行前必须告知用户此操作不可逆。",
        "input_schema": {
            "type": "object",
            "properties": {
                "psd_path": {"type": "string", "description": "PSD 文件绝对路径"},
                "layer_path": {"type": "string", "description": "图层路径"},
                "scale": {"type": "number", "description": "同时按比例缩放（可选）"},
                "width": {"type": "integer", "description": "同时按目标宽度缩放（可选）"},
                "height": {"type": "integer", "description": "同时按目标高度缩放（可选）"},
                "fit_contain": {"type": "string", "description": "同时缩放到盒子内，格式 '800x600'（可选）"}
            },
            "required": ["psd_path", "layer_path"]
        }
    },
]

# ────────────────── 工具执行函数 ──────────────────
# 这些是只读工具，不需要快照
READ_ONLY_TOOLS = {"get_psd_info", "preview_psd", "read_text"}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """执行工具并返回输出字符串"""
    try:
        handlers = {
            "get_psd_info": _get_psd_info,
            "preview_psd": _preview_psd,
            "set_visibility": _set_visibility,
            "set_opacity": _set_opacity,
            "set_blend_mode": _set_blend_mode,
            "rename_layer": _rename_layer,
            "reorder_layer": _reorder_layer,
            "move_layer": _move_layer,
            "set_layer_position": _set_layer_position,
            "remove_layer": _remove_layer,
            "add_layer": _add_layer,
            "resample_layer": _resample_layer,
            "rasterize_layer": _rasterize_layer,
            "create_group": _create_group,
            "export_psd": _export_psd,
            "read_text": _read_text,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"未知工具: {tool_name}"

        logger.info(f"调用工具处理器: {tool_name}")
        return handler(tool_input)
    except Exception as e:
        logger.error(f"工具处理器异常: {tool_name}, 错误: {str(e)}", exc_info=True)
        return f"错误: 工具执行失败 - {str(e)}"


def _run(script: str, args: list[str]) -> str:
    try:
        stdout, stderr, code = run_script(script, args)
        if code != 0:
            error_msg = stderr or stdout or "未知错误"
            logger.error(f"脚本执行失败: {script}, 返回码: {code}, 错误: {error_msg}")
            return f"错误: {error_msg}"
        return stdout or "操作成功"
    except Exception as e:
        logger.error(f"_run 异常: {script}, 错误: {str(e)}", exc_info=True)
        return f"错误: {str(e)}"


def _get_psd_info(inp: dict) -> str:
    return _run("info.py", [inp["psd_path"]])


def _preview_psd(inp: dict) -> str:
    args = [inp["psd_path"]]
    if inp.get("layer"):
        args += ["--layer", inp["layer"]]
    if inp.get("max_size"):
        args += ["--max-size", str(inp["max_size"])]
    return _run("preview.py", args)


def _set_visibility(inp: dict) -> str:
    action_map = {"hide": "--hide", "show": "--show", "toggle": "--toggle"}
    flag = action_map.get(inp["action"], "--toggle")
    return _run("visibility.py", [inp["psd_path"], inp["layer_path"], flag])


def _set_opacity(inp: dict) -> str:
    return _run("opacity.py", [inp["psd_path"], inp["layer_path"], str(inp["value"])])


def _set_blend_mode(inp: dict) -> str:
    return _run("blend_mode.py", [inp["psd_path"], inp["layer_path"], inp["mode"]])


def _rename_layer(inp: dict) -> str:
    return _run("rename.py", [inp["psd_path"], inp["layer_path"], inp["new_name"]])


def _reorder_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("to_index") is not None:
        args += ["--to-index", str(inp["to_index"])]
    elif inp.get("direction") == "up":
        args += ["--up"]
    else:
        args += ["--down"]
    return _run("reorder.py", args)


def _move_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("to_group"):
        args += ["--to-group", inp["to_group"]]
    else:
        args += ["--to-root"]
    return _run("move_layer.py", args)


def _set_layer_position(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("dx") is not None:
        args += ["--dx", str(inp["dx"])]
    if inp.get("dy") is not None:
        args += ["--dy", str(inp["dy"])]
    if inp.get("left") is not None:
        args += ["--left", str(inp["left"])]
    if inp.get("top") is not None:
        args += ["--top", str(inp["top"])]
    return _run("position_layer.py", args)


def _remove_layer(inp: dict) -> str:
    return _run("remove_layer.py", [inp["psd_path"], inp["layer_path"]])


def _add_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["image_path"]]
    if inp.get("name"):
        args += ["--name", inp["name"]]
    if inp.get("width"):
        args += ["--width", str(inp["width"])]
    elif inp.get("height"):
        args += ["--height", str(inp["height"])]
    elif inp.get("scale"):
        args += ["--scale", str(inp["scale"])]
    elif inp.get("fit_contain"):
        args += ["--fit-contain", inp["fit_contain"]]
    elif inp.get("fit_cover"):
        args += ["--fit-cover", inp["fit_cover"]]
    if inp.get("center"):
        args += ["--center"]
    return _run("add_layer.py", args)


def _resample_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("scale"):
        args += ["--scale", str(inp["scale"])]
    elif inp.get("width"):
        args += ["--width", str(inp["width"])]
    elif inp.get("height"):
        args += ["--height", str(inp["height"])]
    elif inp.get("fit_contain"):
        args += ["--fit-contain", inp["fit_contain"]]
    return _run("resample_layer.py", args)


def _create_group(inp: dict) -> str:
    args = [inp["psd_path"], inp["group_name"]]
    if inp.get("layers"):
        args += ["--layers", inp["layers"]]
    return _run("create_group.py", args)


def _export_psd(inp: dict) -> str:
    args = [inp["psd_path"], inp["output_path"]]
    if inp.get("quality"):
        args += ["--quality", str(inp["quality"])]
    if inp.get("max_size"):
        args += ["--max-size", str(inp["max_size"])]
    return _run("export.py", args)


def _read_text(inp: dict) -> str:
    return _run("read_text.py", [inp["psd_path"], inp["layer_path"]])


def _rasterize_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("scale"):
        args += ["--scale", str(inp["scale"])]
    elif inp.get("width"):
        args += ["--width", str(inp["width"])]
    elif inp.get("height"):
        args += ["--height", str(inp["height"])]
    elif inp.get("fit_contain"):
        args += ["--fit-contain", inp["fit_contain"]]
    return _run("rasterize_layer.py", args)
