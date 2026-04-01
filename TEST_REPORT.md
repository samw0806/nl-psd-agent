# 图层移动功能测试报告

**测试日期：** 2026-04-01  
**测试文件：** examples/test_100009151672.psb  
**测试目标：** 验证两个入口（CLI 和 Web API）的图层移动功能一致性

---

## 测试概述

项目中存在三种不同的图层移动功能：

1. **坐标位置移动**（上下左右像素移动）- `position_layer.py`
2. **图层组间移动**（移动到不同组或根层）- `move_layer.py`
3. **图层堆叠顺序移动**（上移/下移）- `reorder.py`

---

## 测试结果总结

| 功能 | CLI 测试 | Web API 代码审查 | 一致性 | 状态 |
|------|---------|-----------------|--------|------|
| 坐标位置移动（相对位移） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 坐标位置移动（绝对定位） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 坐标位置移动（组图层拒绝） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 图层堆叠顺序移动（上移） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 图层堆叠顺序移动（下移） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 图层组间移动（移到组） | ✅ 通过 | ✅ 一致 | ✅ | PASS |
| 图层组间移动（移到根层） | ✅ 通过 | ✅ 一致 | ✅ | PASS |

**总体结论：** ✅ 所有测试通过，两个入口的功能完全一致

---

## 详细测试记录

### 测试 1：坐标位置移动 - 相对位移

**测试命令：**
```bash
python scripts/position_layer.py examples/test_100009151672.psb "背景" --dx 50 --dy 30
```

**测试结果：**
```
图层 '背景' 已更新位置
  旧位置: left=0, top=0
  新位置: left=50, top=30
  位移量: dx=50, dy=30
文件已保存到 examples/test_100009151672.psb
```

**验证：**
```bash
python scripts/info.py examples/test_100009151672.psb | grep "^\├── \[Pixel\] 背景"
```

**输出：**
```
├── [Pixel] 背景                   | 可见 | 不透明度:100% | normal | 位置:(50,30) 尺寸:800×800
```

**Web API 对应实现：**
```python
# backend/tools.py 第 381-391 行
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
```

**一致性分析：** ✅ Web API 直接调用相同的 `position_layer.py` 脚本，参数传递逻辑一致

---

### 测试 2：坐标位置移动 - 绝对定位

**测试命令：**
```bash
python scripts/position_layer.py examples/test_100009151672.psb "背景" --left 100 --top 200
```

**测试结果：**
```
图层 '背景' 已更新位置
  旧位置: left=50, top=30
  新位置: left=100, top=200
  位移量: dx=50, dy=170
文件已保存到 examples/test_100009151672.psb
```

**验证：**
```
├── [Pixel] 背景                   | 可见 | 不透明度:100% | normal | 位置:(100,200) 尺寸:800×800
```

**一致性分析：** ✅ 绝对定位功能正常，Web API 使用相同脚本

---

### 测试 3：坐标位置移动 - 组图层拒绝

**测试命令：**
```bash
python scripts/position_layer.py examples/test_100009151672.psb "主品" --dx 10 --dy 10
```

**测试结果：**
```
错误：图层 '主品' 是组图层，当前仅支持移动非组图层。请先分别移动组内子图层。
退出码: 1
```

**一致性分析：** ✅ 组图层被正确拒绝，错误信息清晰。Web API 调用相同脚本，会返回相同错误

---

### 测试 4：图层堆叠顺序移动 - 下移

**测试命令：**
```bash
python scripts/reorder.py examples/test_100009151672.psb "背景" --down
```

**测试结果：**
```
图层 '背景' 已下移 (索引 0 → 1)
文件已保存到 examples/test_100009151672.psb
```

**验证：**
```bash
python scripts/info.py examples/test_100009151672.psb | grep -A 1 "图层结构:"
```

**输出：**
```
图层结构:
├── [Group] 主品                   | 可见 | 不透明度:100% | pass_through | 位置:(-368,-371) 尺寸:1900×1414
```

**说明：** 背景图层原本在索引 0（最上层），下移后到索引 1，主品图层现在在最上层

**Web API 对应实现：**
```python
# backend/tools.py 第 361-369 行
def _reorder_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("to_index") is not None:
        args += ["--to-index", str(inp["to_index"])]
    elif inp.get("direction") == "up":
        args += ["--up"]
    else:
        args += ["--down"]
    return _run("reorder.py", args)
```

**一致性分析：** ✅ Web API 调用相同脚本，参数逻辑一致

---

### 测试 5：图层堆叠顺序移动 - 上移

**测试命令：**
```bash
python scripts/reorder.py examples/test_100009151672.psb "背景" --up
```

**测试结果：**
```
图层 '背景' 已上移 (索引 1 → 0)
文件已保存到 examples/test_100009151672.psb
```

**一致性分析：** ✅ 上移功能正常，背景图层恢复到最上层

---

### 测试 6：图层组间移动 - 移到组

**测试命令：**
```bash
python scripts/move_layer.py examples/test_100009151672.psb "背景" --to-group "双券"
```

**测试结果：**
```
图层 '背景' 已移动到 '双券'
文件已保存到 examples/test_100009151672.psb
```

**验证：**
```bash
python scripts/info.py examples/test_100009151672.psb | grep -B 1 "^\│   └── \[Pixel\] 背景"
```

**输出：**
```
│   │   └── [Type] 店铺会员券                | 可见 | 不透明度:100% | normal | 文字:"店铺会员券" | 位置:(35,92) 尺寸:52×11
│   └── [Pixel] 背景                   | 可见 | 不透明度:100% | normal | 位置:(100,200) 尺寸:800×800
```

**说明：** 背景图层成功移动到双券组下（作为双券组的最后一个子图层）

**Web API 对应实现：**
```python
# backend/tools.py 第 372-378 行
def _move_layer(inp: dict) -> str:
    args = [inp["psd_path"], inp["layer_path"]]
    if inp.get("to_group"):
        args += ["--to-group", inp["to_group"]]
    else:
        args += ["--to-root"]
    return _run("move_layer.py", args)
```

**一致性分析：** ✅ Web API 调用相同脚本，参数逻辑一致

---

### 测试 7：图层组间移动 - 移到根层

**测试命令：**
```bash
python scripts/move_layer.py examples/test_100009151672.psb "双券/背景" --to-root
```

**测试结果：**
```
图层 '双券/背景' 已移动到 '根层'
文件已保存到 examples/test_100009151672.psb
```

**验证：**
```bash
python scripts/info.py examples/test_100009151672.psb | grep -E "^(├──|└──) \[Pixel\] 背景"
```

**输出：**
```
└── [Pixel] 背景                   | 可见 | 不透明度:100% | normal | 位置:(100,200) 尺寸:800×800
```

**说明：** 背景图层成功移回根层（在最底部，使用 └── 表示最后一个根层图层）

**一致性分析：** ✅ 移到根层功能正常，Web API 使用相同脚本

---

## Web API 一致性验证

### Tool 定义对比

| 功能 | CLI 脚本 | Web API Tool 名称 | Tool 定义位置 | 执行函数位置 |
|------|---------|------------------|--------------|-------------|
| 坐标位置移动 | position_layer.py | set_layer_position | tools.py:161-175 | tools.py:381-391 |
| 图层组间移动 | move_layer.py | move_layer | tools.py:147-159 | tools.py:372-378 |
| 图层堆叠顺序移动 | reorder.py | reorder_layer | tools.py:133-145 | tools.py:361-369 |

### 参数映射验证

#### 1. set_layer_position

**Tool 参数：**
- `psd_path` (string)
- `layer_path` (string)
- `dx` (integer, optional) - x 方向相对位移
- `dy` (integer, optional) - y 方向相对位移
- `left` (integer, optional) - 目标 left 坐标
- `top` (integer, optional) - 目标 top 坐标

**CLI 脚本参数：**
- `psd_file` (positional)
- `layer_path` (positional)
- `--dx` (optional)
- `--dy` (optional)
- `--left` (optional)
- `--top` (optional)

**映射逻辑：** ✅ 完全一致，Web API 将 JSON 参数转换为 CLI 参数

#### 2. move_layer

**Tool 参数：**
- `psd_path` (string)
- `layer_path` (string)
- `to_group` (string, optional) - 目标组路径
- `to_root` (boolean, optional) - 是否移到顶层

**CLI 脚本参数：**
- `psd_file` (positional)
- `layer_path` (positional)
- `--to-group` (optional)
- `--to-root` (flag)

**映射逻辑：** ✅ 完全一致

#### 3. reorder_layer

**Tool 参数：**
- `psd_path` (string)
- `layer_path` (string)
- `direction` (string, enum: ["up", "down"])
- `to_index` (integer, optional) - 移动到指定索引

**CLI 脚本参数：**
- `psd_file` (positional)
- `layer_path` (positional)
- `--up` (flag)
- `--down` (flag)
- `--to-index` (optional)

**映射逻辑：** ✅ 完全一致，direction 参数正确转换为 --up 或 --down 标志

---

## 代码审查发现

### 1. 执行机制一致性

所有 Web API Tool 都通过 `_run()` 函数调用相同的 CLI 脚本：

```python
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
```

**结论：** ✅ Web API 不是重新实现功能，而是直接调用 CLI 脚本，确保了行为的完全一致性

### 2. 错误处理一致性

- CLI 脚本的错误信息通过 stderr 返回
- Web API 捕获 stderr 并返回给前端
- 错误信息格式一致

**结论：** ✅ 错误处理机制一致

### 3. 虚拟环境处理

```python
VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"

def _python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable
```

**结论：** ✅ Web API 正确使用项目虚拟环境中的 Python，与 CLI 环境一致

---

## 文档一致性检查

### CLAUDE.md vs AGENTS.md

**对比结果：** ✅ 两个文档的内容完全一致

**能力描述（第 12 行）：**
- CLAUDE.md: "移动非组图层的位置（left/top 坐标）"
- AGENTS.md: "移动非组图层的位置（left/top 坐标）"

**脚本速查表（第 61-63 行）：**
- 两个文档的脚本列表、示例命令完全相同

### 文档准确性评估

**发现的问题：**

1. **能力描述不够详细**
   - 当前只提到"移动非组图层的位置"
   - 未明确区分三种移动功能：坐标移动、组间移动、堆叠顺序移动

2. **限制描述可能引起误解**
   - CLAUDE.md 第 43 行："Photoshop 式原生变换（任意图层的自由移动/缩放/旋转）"
   - 这里说"不能自由移动"，但实际上非组图层可以通过 position_layer.py 进行坐标移动
   - 应该明确区分"坐标移动"（支持）和"带变换矩阵的复杂变换"（不支持）

**建议改进：** 见下一节

---

## 建议改进

### 1. 更新文档描述

**CLAUDE.md 和 AGENTS.md 的"你的能力"部分，建议修改为：**

```markdown
你可以：
- 打开和查看 PSD/PSB 文件结构（图层树、文档信息）
- **看到**文件的视觉效果（通过 preview.py 导出图片后查看）
- 切换图层可见性、调整不透明度、更改混合模式
- 重命名、删除图层
- **移动非组图层的坐标位置**（相对位移或绝对定位）
- **将图层移动到不同的组或移到根层**
- **改变图层在同级中的堆叠顺序**（上移/下移）
- 从外部图片添加新像素图层（支持插入前缩放：等比缩放、contain、cover、居中放置）
- 对普通像素图层执行重建式缩放（删旧层、造新层）
- 创建和管理图层组
- 读取文字图层内容（但不能修改文字）
- 提取智能对象中的嵌入文件
- 导出为 PNG/JPG
- 保存修改后的 PSD 文件

你不能：
- 修改文字图层的内容（psd-tools 硬限制）
- 编辑形状图层或智能对象的矢量/嵌入内容
- 添加/修改图层样式（投影、描边、发光等）
- 应用/修改调整图层效果
- **对组图层整体进行坐标移动**（需分别移动子图层）
- **对任意图层进行旋转操作**
- **对任意图层进行带变换矩阵的复杂变换**
- 保证文字图层、形状图层、智能对象在缩放后仍保持原语义
```

### 2. 更新 .agents/skills/psd-editor/SKILL.md

**能力边界部分，建议修改为：**

```markdown
## 能力边界

✅ 可以：图层显隐、不透明度、混合模式、重命名、排序、删除、
          移动非组图层坐标（相对位移/绝对定位）、图层组间移动、
          图层堆叠顺序调整、添加像素图层（含插入前缩放）、
          像素图层重建式缩放、创建组、导出 PNG/JPG、
          读取文字内容、提取智能对象文件

❌ 不能：修改文字内容、编辑形状/智能对象、图层样式、
          调整图层、组图层整体坐标移动、图层旋转、
          带变换矩阵的复杂变换
```

---

## 测试环境

- **操作系统：** Linux (WSL2)
- **Python 版本：** 3.12
- **虚拟环境：** /home/sam/code/nl-psd-agent/.venv
- **关键依赖：** psd-tools, Pillow
- **测试文件大小：** 192MB (PSB 格式)
- **图层数量：** 150 层

---

## 结论

### 功能一致性

✅ **两个入口的图层移动功能完全一致**

- CLI 入口直接调用 Python 脚本
- Web API 通过 FastAPI 后端调用相同的 Python 脚本
- 参数映射逻辑正确，无差异
- 错误处理机制一致
- 虚拟环境配置一致

### 测试覆盖率

✅ **所有三种移动功能均已测试**

1. 坐标位置移动（相对位移、绝对定位、组图层拒绝）
2. 图层堆叠顺序移动（上移、下移）
3. 图层组间移动（移到组、移到根层）

### 文档准确性

⚠️ **文档描述存在改进空间**

- 能力描述不够详细，未明确区分三种移动功能
- 限制描述可能引起误解（"不能自由移动"实际上非组图层可以坐标移动）
- 建议按照上述"建议改进"部分更新文档

### 最终评估

**状态：** ✅ PASS  
**置信度：** 高  
**建议：** 可以放心使用两个入口，功能行为完全一致。建议更新文档以提高准确性。

---

## 附录：测试文件清理

测试完成后，可以删除测试副本：

```bash
rm examples/test_100009151672.psb
```

原始文件 `examples/100009151672.psb` 未被修改。
