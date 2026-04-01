# 修复：rasterize_layer 两个 Bug（中文乱码 + 黑色区域）

**日期**：2026-04-01  
**状态**：待实施

---

## 问题描述

对 Smart Object 图层执行 `rasterize_layer` 后，发现两个 Bug：

1. **中文图层名乱码**：图层名"待替换"变成了"ÂæÖÊõøÊç¢"
2. **黑色区域**：栅格化后图层图像中出现黑色不透明区域（原本应该是透明）

---

## Bug 1：中文图层名乱码

### 根本原因

`psd.create_pixel_layer()` 内部的 `_build_layer_record_and_channels` 只写入 pascal string（`record.name`），**不写** `UNICODE_LAYER_NAME` tagged block（`luni`）。

`_utils.py` 的 monkey patch 把 pascal string 编码改成了 UTF-8，但读取端 `read_pascal_string` 仍用 macroman 解码，造成"写 UTF-8 / 读 macroman"不对称 → 乱码。

`Layer.name.setter` 会正确写入 `luni` tagged block（UTF-16-BE），读取时走该路径就完全绕过 pascal string 编码问题。

### 修复方法

在每次 `create_pixel_layer(img, name=..., ...)` 调用之后，立即通过 setter 重新赋一次名称：

```python
new_layer = psd.create_pixel_layer(img, name=old_name, ...)
new_layer.name = old_name  # 触发 UNICODE_LAYER_NAME tagged block 写入，避免中文乱码
```

### 受影响文件

| 文件 | 行号 | 修改内容 |
|---|---|---|
| `scripts/rasterize_layer.py` | 122 | `create_pixel_layer` 后补 `new_layer.name = old_name` |
| `scripts/resample_layer.py` | 112 | `create_pixel_layer` 后补 `new_layer.name = old_name` |
| `scripts/add_layer.py` | 152 | `create_pixel_layer` 后补 `new_layer.name = layer_name` |

---

## Bug 2：图像出现黑色区域

### 根本原因

`layer.composite()` 默认参数是 `color=1.0, alpha=0.0`。内部 `paste()` 用 `background=1.0`（白色）初始化 color 通道，但 shape/alpha 通道用 0 初始化。当 `force=False`（默认）时，compositor 可能走缓存路径跳过 alpha channel，导致返回 RGB 而非 RGBA，后续 `.convert("RGBA")` 以 alpha=255 填充，把黑色背景固化进去。

### 修复方法

传入 `color=0.0, alpha=0.0, force=True`：

- `color=0.0`：背景初始化为黑色（透明区域最终 alpha=0，颜色无关紧要）
- `alpha=0.0`：背景完全透明
- `force=True`：强制完全重渲染，`skip_alpha=False`，保证结果包含 alpha 通道

```python
# 修复前（scripts/rasterize_layer.py:78）
img = layer.composite()

# 修复后
img = layer.composite(color=0.0, alpha=0.0, force=True)
```

### 受影响文件

| 文件 | 行号 | 修改内容 |
|---|---|---|
| `scripts/rasterize_layer.py` | 78 | `layer.composite()` → `layer.composite(color=0.0, alpha=0.0, force=True)` |

---

## 完整修改清单

| 文件 | 行号 | 修改内容 |
|---|---|---|
| `scripts/rasterize_layer.py` | 78 | composite 加参数 `color=0.0, alpha=0.0, force=True` |
| `scripts/rasterize_layer.py` | 122 | create_pixel_layer 后补 `new_layer.name = old_name` |
| `scripts/resample_layer.py` | 112 | create_pixel_layer 后补 `new_layer.name = old_name` |
| `scripts/add_layer.py` | 152 | create_pixel_layer 后补 `new_layer.name = layer_name` |

`scripts/_utils.py` 不修改。

---

## 验证方法

```bash
# Bug 1：栅格化后图层名不乱码
.venv/bin/python scripts/rasterize_layer.py test.psd "主品/100009151672-1待替换" --scale 0.5
.venv/bin/python scripts/info.py test.psd | grep "待替换"
# 期望：图层名仍显示"待替换"，不出现乱码

# Bug 2：无黑色区域
.venv/bin/python scripts/preview.py test.psd
# 期望：preview.png 中该图层背景透明，无黑色
```
