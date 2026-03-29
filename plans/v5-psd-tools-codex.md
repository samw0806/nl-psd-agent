# 自然语言 PSD Agent -- v5 psd-tools + Codex 纯 CLI 方案

> **版本**: v5
> **更新日期**: 2026-03-27
> **状态**: 讨论稿
> **核心思路**: 放弃 Photopea / 浏览器方案，用 psd-tools (Python) 作为 PSD 引擎，配合 Codex Skills 和脚本，实现纯终端下的自然语言 PSD 操作

---

## 一、为什么选 psd-tools？与 v4 方案的对比

### v4 (Photopea) 的痛点

| 痛点 | 说明 |
|------|------|
| 必须有浏览器 | Photopea 只能在 iframe 中运行，不能无头 |
| 需要 Bridge 层 | Codex → MCP Bridge → WebSocket → Browser → Photopea，链路长且脆弱 |
| Agent 是"盲的" | 需要额外接 Playwright MCP 截图，Agent 才能"看"到效果 |
| 启动流程复杂 | 启动 Bridge + Web Server + 浏览器 + Codex，至少 3 个进程 |
| 第三方依赖 | Photopea 是个人项目，长期风险高 |

### v5 (psd-tools) 的优势

| 优势 | 说明 |
|------|------|
| **纯 CLI，零浏览器** | 所有操作在终端完成，`cd 项目目录 && codex` 就开始 |
| **Agent 有"眼睛"** | psd-tools composite → PNG → Codex 视觉模型直接看图 |
| **零 Bridge** | Codex 直接 `python scripts/xxx.py`，无中间层 |
| **启动极简** | 一个终端，一个命令 |
| **开源可控** | psd-tools 是 MIT 协议，1.3k+ stars，Python 生态 |

### 取舍

| 放弃的能力 | 说明 |
|------------|------|
| 文字图层编辑 | psd-tools **不支持修改文字内容**（能读不能写） |
| 形状图层编辑 | 不支持 |
| 智能对象编辑 | 不支持（但能读取嵌入文件） |
| 实时渲染预览 | 每次需要重新 composite 导出查看 |
| 手动拖拉拽 | 没有 GUI，纯命令行 |

**核心原则：psd-tools 能做什么，Agent 的能力边界就到哪里。**

---

## 二、psd-tools 能力全景（v1.14.2）

### 2.1 文件级操作

| 操作 | API | 状态 |
|------|-----|------|
| 打开 PSD | `PSDImage.open('file.psd')` | ✅ 完全支持 |
| 打开 PSB | `PSDImage.open('file.psb')` | ✅ 支持（小尺寸 PSB 无问题） |
| 保存 PSD | `psd.save('output.psd')` | ✅ 支持 |
| 保存 PSB | `psd.save('output.psb')` | ⚠️ 支持，大尺寸 >30000px 曾有 bug（v1.9.16 已修复） |
| 从头创建 PSD | `PSDImage.new(mode, size, depth)` | ✅ 支持 |
| 从 PIL 创建 | `PSDImage.frompil(pil_image)` | ✅ 支持 |
| 文档信息 | `psd.mode`, `psd.size`, `psd.depth`, `psd.channels` | ✅ 只读 |

### 2.1.1 与 Pillow 组合后的素材处理能力

虽然 `psd-tools` 本身没有 Photoshop 那种原生 transform API，但它和 `Pillow` 组合后，可以覆盖一部分非常实用的“缩放素材”场景：

| 场景 | 做法 | 状态 |
|------|------|------|
| 插入外部商品图时先缩放 | `Image.open()` → `resize()` / `thumbnail()` → `create_pixel_layer()` | ✅ 推荐 |
| 按指定宽度等比缩放后插入 | 先算目标高，再 `resize()` | ✅ 推荐 |
| 按指定高度等比缩放后插入 | 先算目标宽，再 `resize()` | ✅ 推荐 |
| 按盒子区域 contain / cover | 先算缩放比例，再裁剪或留白 | ✅ 可实现 |
| 已有像素图层重新缩放 | 导出图层图像 → Pillow 重采样 → 删除旧层 → 新建新层 | ⚠️ 可实现，但属于“重建式缩放” |

### 2.2 图层读取（全部图层类型）

| 图层类型 | 类 | 可读信息 |
|---------|-----|---------|
| 像素图层 | `PixelLayer` | 名称、位置、像素数据、蒙版 |
| 图层组 | `Group` | 名称、子图层、嵌套结构 |
| 文字图层 | `TypeLayer` | **文字内容** (`layer.text`)、字体、字号、段落样式、字符样式 |
| 形状图层 | `ShapeLayer` | 矢量蒙版、路径数据 |
| 智能对象 | `SmartObjectLayer` | 嵌入文件数据（可提取 JPG/PNG 等） |
| 调整图层 | `AdjustmentLayer` | 类型信息 |
| 填充图层 | `SolidColorFill` / `PatternFill` / `GradientFill` | 填充参数 |

### 2.3 图层属性修改（可写属性）

| 属性 | API | 类型 |
|------|-----|------|
| 名称 | `layer.name = "新名字"` | str |
| 可见性 | `layer.visible = True/False` | bool |
| 不透明度 | `layer.opacity = 128` | int (0-255) |
| 混合模式 | `layer.blend_mode = BlendMode.SCREEN` | BlendMode 枚举 |
| 剪贴蒙版 | `layer.clipping = True/False` | bool |

### 2.4 图层结构操作

| 操作 | API |
|------|-----|
| 遍历图层 | `for layer in psd:` / `psd.descendants()` |
| 索引访问 | `psd[0]`, `group[1]` |
| 添加图层 | `group.append(layer)` |
| 插入图层 | `group.insert(index, layer)` |
| 删除图层 | `group.remove(layer)` / `group.pop()` |
| 清空组 | `group.clear()` |
| 上移/下移 | `layer.move_up()` / `layer.move_down()` |
| 跨组移动 | `target_group.append(layer)` |
| 创建像素图层 | `psd.create_pixel_layer(pil_image, name, top, left, opacity)` |
| 创建组 | `psd.create_group(name)` |
| 批量建组 | `psd.create_group(layer_list=[...], name="组名")` |

### 2.5 图像导出与合成

| 操作 | API | 说明 |
|------|-----|------|
| 合成整个文档 | `psd.composite()` | → PIL Image |
| 合成单个图层 | `layer.composite()` | 含蒙版和剪贴层 |
| 原始像素 | `layer.topil()` | 不含蒙版的原始图层 |
| 蒙版导出 | `layer.mask.topil()` | 图层蒙版 |
| NumPy 数组 | `psd.numpy()` / `layer.numpy()` | 供数值处理 |
| 带过滤合成 | `psd.composite(layer_filter=lambda l: ...)` | 可选择性合成 |
| CLI 导出 | `psd-tools export file.psd out.png` | 命令行工具 |

### 2.6 文字图层详细读取

```python
# 读取文字内容
text = layer.text  # "Hello World"

# 读取排版细节
for paragraph in layer.typesetting:
    print(paragraph.style.justification)  # 对齐方式
    for run in paragraph:
        print(run.text)        # 文字片段
        print(run.style.font_name)   # 字体名
        print(run.style.font_size)   # 字号
        # 还有颜色、粗体、斜体等
```

> **注意：文字内容只读，不能修改。** 这是 psd-tools 最大的限制。

### 2.7 不支持的操作

| 操作 | 说明 |
|------|------|
| ❌ 修改文字内容 | TypeLayer 的 text 是只读的 |
| ❌ 编辑形状图层 | 矢量路径只读 |
| ❌ 编辑智能对象 | 嵌入文件只能读取，不能替换 |
| ❌ 调整图层效果 | 不能修改亮度/对比度/色相等调整参数 |
| ❌ 图层样式 | 投影/描边/发光等不能编辑 |
| ❌ 字体渲染 | 不能把文字渲染成像素 |
| ❌ 原生变换操作 | 没有直接的移动/缩放/旋转 API（需要 low-level hack） |

### 2.8 缩放相关能力边界（本版新增）

这里需要把“缩放”拆开理解，否则很容易把 `psd-tools` 的能力想得过大。

#### 方案 1：插入前缩放外部素材

这是本项目里**最推荐、最稳定**的缩放方式。

流程：

1. 用 `Pillow` 打开外部图片
2. 根据用户要求计算目标尺寸
3. 先在内存里缩放图片
4. 再通过 `psd.create_pixel_layer()` 插入为新图层

这个方案适合：

- 白底商品图
- 抠好的产品 PNG
- Logo、角标、贴纸等外部素材
- “放到画布中央，宽度 600px”这类明确的版式要求

这个方案不等于“对已有 PSD 图层做 transform”，而是“**以目标尺寸插入新图层**”。

#### 方案 2：对已有像素图层做重建式缩放

这个方案只适用于**普通像素图层**。

流程：

1. 通过 `layer.composite()` 或 `layer.topil()` 取出当前图层图像
2. 用 `Pillow` 做重采样缩放
3. 记录原图层的基础属性：名称、可见性、不透明度、混合模式、父组、层级顺序、位置
4. 删除原图层
5. 创建一个新的像素图层，放回原位置附近
6. 尽量恢复基础属性

它能实现“视觉上缩放了”，但本质上不是 Photoshop 的原生缩放，而是“**删旧层，造新层**”。

#### 明确不承诺的情况

以下情况不应该宣称“支持缩放”：

- 文字图层缩放且保持可编辑文字
- 形状图层缩放且保持矢量可编辑
- 智能对象缩放且保持智能对象语义
- 保留所有 mask / clip / effect / smart object metadata 的无损缩放
- 完全等价于 Photoshop Free Transform

#### 风险说明

方案 2 的主要风险：

- 可能丢失图层蒙版
- 可能丢失 clipping 关系
- 可能丢失部分高级元数据
- 如果原层不是纯像素层，重建后语义会退化成普通像素图层
- 图层边界框与原始位置恢复需要额外计算

因此，v5 里的推荐原则是：

- **默认优先方案 1**
- **只有当目标层明确是像素图层时，才允许方案 2**
- **对非像素图层，明确提示“不支持原生缩放”**

---

## 三、Agent 能力范围定义

基于 psd-tools 的能力，Agent 能做以下事情：

### Tier 1：核心能力（高可靠性）

| 用户说 | Agent 做 |
|--------|---------|
| "打开 banner.psd" | `PSDImage.open()` 加载文件 |
| "这个 PSD 里有什么？" | 解析图层树 + composite 导出预览图 → 视觉模型查看 |
| "某某图层长什么样？" | `layer.composite()` 导出 → 视觉模型查看 |
| "隐藏 Background 图层" | `layer.visible = False` + `psd.save()` |
| "把 Logo 图层设为 50% 透明" | `layer.opacity = 128` |
| "把图层混合模式改成叠加" | `layer.blend_mode = BlendMode.OVERLAY` |
| "重命名图层为 xxx" | `layer.name = "xxx"` |
| "删除这个图层" | `group.remove(layer)` |
| "把这个图层移到那个组里" | `target.append(layer)` |
| "把图层上移/下移" | `layer.move_up()` / `layer.move_down()` |
| "导出为 PNG" | `psd.composite().save('out.png')` |
| "导出某个图层" | `layer.composite().save('layer.png')` |
| "保存修改" | `psd.save('output.psd')` |

### Tier 2：进阶能力（需要组合操作）

| 用户说 | Agent 做 |
|--------|---------|
| "往这个 PSD 里加一张图片作为新图层" | 打开图片 → `psd.create_pixel_layer(pil_img)` |
| "插入这张商品图，宽度缩到 600px" | Pillow 先等比缩放 → `create_pixel_layer()` |
| "把商品图放进 800×800 盒子里，完整显示" | Pillow 先按 contain 规则缩放 → 再插入 |
| "把这些图层归到一个新组" | `psd.create_group(layer_list=[...])` |
| "只导出可见图层的合成" | `psd.composite(layer_filter=lambda l: l.is_visible())` |
| "导出所有图层各自的 PNG" | 遍历 + `layer.composite()` + save |
| "读一下这个文字图层写的什么" | `layer.text` + `layer.typesetting` |
| "提取智能对象里的原始文件" | `layer.smart_object.data` → 保存 |
| "替换某个像素图层的内容" | 删除旧图层 → 创建新像素图层到同一位置 |
| "把这个像素图层缩小 50%" | 导出像素图层 → Pillow 重采样 → 删除并重建图层 |

### Tier 3：Agent 做不到的（明确告知用户）

| 用户说 | Agent 回应 |
|--------|-----------|
| "把标题改成 xxx" | "抱歉，psd-tools 不支持修改文字内容。建议在 Photoshop 中手动修改。" |
| "给图层加个投影效果" | "抱歉，图层样式编辑不支持。" |
| "把这个文字图层缩小 50%" | "抱歉，psd-tools 不支持文字图层的原生缩放。建议在 Photoshop / Photopea 中处理。" |
| "把这个智能对象缩小 50%" | "抱歉，v5 不支持保持智能对象语义的缩放。" |
| "像 Photoshop 一样自由缩放任意图层" | "抱歉，v5 不提供原生 transform，只支持外部素材插入前缩放，以及像素图层的重建式缩放。" |
| "调亮一点" | "抱歉，调整图层操作不支持。" |

---

## 四、核心亮点：Agent 有"眼睛"

### 4.1 视觉能力链路

```
psd-tools composite() → PIL Image → 保存为 PNG/JPG → Codex 视觉模型读取图片

这意味着：
- Agent 能看到整个文档的合成效果
- Agent 能看到单个图层长什么样
- Agent 能在操作前后对比效果
- Agent 能根据视觉反馈判断操作是否正确
```

### 4.2 比 Photopea 方案更好的"视觉"

| 对比项 | v4 Photopea | v5 psd-tools |
|--------|------------|-------------|
| Agent 看全图 | 需 Playwright 截图（额外 MCP） | `psd.composite()` → PNG，直接读 |
| Agent 看单层 | 很难做到 | `layer.composite()` → PNG，直接读 |
| 看操作前后对比 | 需两次截图，复杂 | 操作前后各 composite，自然对比 |
| 延迟 | 截图传输 + 编码 | 本地文件读取，快 |
| Token 消耗 | 全屏截图很大 | 可控制导出尺寸/区域 |

### 4.3 实际"看"的工作流

```
用户: "打开 banner.psd，告诉我里面有什么"

Agent 内部:
  1. python scripts/info.py banner.psd          → 获取图层树文本
  2. python scripts/preview.py banner.psd        → 导出 .tmp/preview.png
  3. [Codex 视觉模型读取 .tmp/preview.png]
  4. 向用户描述：
     "这是一个 1920×1080 的横幅设计，包含：
      - 顶部有一个红色标题写着'Summer Sale'
      - 中间是一张运动鞋产品图
      - 底部有价格信息'$99.99'
      - 背景是蓝色渐变
      共 15 个图层，分为 Header、Body、Background 三个组。"

用户: "把 Header 组里的 Logo 图层隐藏掉"

Agent 内部:
  1. python scripts/visibility.py banner.psd "Header/Logo" --hide
  2. python scripts/preview.py banner.psd        → 导出新的 preview.png
  3. [Codex 视觉模型读取新的 preview.png]
  4. "已隐藏 Logo 图层。现在顶部只剩标题文字，Logo 位置空出来了。"
```

---

## 五、项目结构

```
nl-psd-agent/
├── AGENTS.md                          # Codex 项目指引（核心！）
├── README.md                          # 项目说明 + 使用方法
├── requirements.txt                   # Python 依赖
│
├── scripts/                           # Python CLI 脚本（Agent 的"手脚"）
│   ├── info.py                        # 显示 PSD 信息 + 图层树
│   ├── preview.py                     # 合成预览（整个文档或指定图层）
│   ├── visibility.py                  # 切换图层可见性
│   ├── opacity.py                     # 设置图层不透明度
│   ├── blend_mode.py                  # 设置混合模式
│   ├── rename.py                      # 重命名图层
│   ├── reorder.py                     # 图层排序（上移/下移）
│   ├── move_layer.py                  # 移动图层到其他组
│   ├── remove_layer.py                # 删除图层
│   ├── add_layer.py                   # 从图片添加新像素图层
│   ├── resample_layer.py              # 对已有像素图层做重建式缩放
│   ├── create_group.py                # 创建图层组
│   ├── export.py                      # 导出为 PNG/JPG
│   ├── export_layers.py               # 批量导出所有图层
│   ├── extract_smart_object.py        # 提取智能对象内容
│   ├── read_text.py                   # 读取文字图层内容和样式
│   └── save.py                        # 保存 PSD 文件
│
├── .agents/                           # Codex Skills
│   └── skills/
│       └── psd-editor/
│           └── SKILL.md               # PSD 编辑核心 Skill
│
├── .tmp/                              # 临时文件（预览图、导出图）
│   └── .gitkeep
│
├── plans/                             # 架构设计文档
│   ├── v1-architecture.md
│   ├── v2-architecture.md
│   ├── v3-frontend-design.md
│   ├── v4-codex-implementation-discussion.md
│   └── v5-psd-tools-codex.md          # ← 本文档
│
└── examples/                          # 示例 PSD 文件（用于测试）
    └── README.md
```

---

## 六、脚本设计

每个脚本都是**独立的 CLI 工具**，接收命令行参数，输出结构化文本。Codex 通过 shell 执行这些脚本。

### 6.1 info.py — 查看 PSD 信息

```
用法: python scripts/info.py <psd_file> [--depth N]

输出:
  文件: banner.psd
  尺寸: 1920 × 1080 px
  色彩模式: RGB
  位深: 8
  图层数: 15

  图层结构:
  ├── [Group] Header
  │   ├── [Pixel] Logo          | 可见 | 不透明度:255 | 正常
  │   ├── [Type]  Title         | 可见 | 不透明度:255 | 正常 | 文字:"Summer Sale"
  │   └── [Type]  Subtitle      | 可见 | 不透明度:200 | 正常 | 文字:"Up to 50% off"
  ├── [Group] Body
  │   ├── [Smart] Product Image | 可见 | 不透明度:255 | 正常
  │   └── [Type]  Price         | 可见 | 不透明度:255 | 正常 | 文字:"$99.99"
  └── [Pixel] Background        | 可见 | 不透明度:255 | 正常
```

### 6.2 preview.py — 生成预览图

```
用法:
  python scripts/preview.py <psd_file>                      # 合成整个文档
  python scripts/preview.py <psd_file> --layer "Header/Logo" # 合成指定图层
  python scripts/preview.py <psd_file> --all-layers          # 导出所有图层各自的图
  python scripts/preview.py <psd_file> --max-size 800        # 限制输出尺寸

输出:
  预览已保存到 .tmp/preview.png (1920×1080)
```

### 6.3 visibility.py — 切换可见性

```
用法:
  python scripts/visibility.py <psd_file> "Background" --hide
  python scripts/visibility.py <psd_file> "Header/Logo" --show
  python scripts/visibility.py <psd_file> "Header/Logo" --toggle

输出:
  ✓ 图层 'Background' 已隐藏
  文件已保存到 banner.psd
```

### 6.4 opacity.py — 设置不透明度

```
用法:
  python scripts/opacity.py <psd_file> "Header/Title" 128    # 0-255

输出:
  ✓ 图层 'Title' 不透明度: 255 → 128 (50%)
  文件已保存到 banner.psd
```

### 6.5 blend_mode.py — 设置混合模式

```
用法:
  python scripts/blend_mode.py <psd_file> "Header/Logo" multiply
  python scripts/blend_mode.py --list   # 列出所有支持的混合模式

支持的混合模式:
  normal, dissolve, darken, multiply, color_burn, linear_burn,
  lighten, screen, color_dodge, linear_dodge, overlay, soft_light,
  hard_light, vivid_light, linear_light, pin_light, hard_mix,
  difference, exclusion, hue, saturation, color, luminosity
```

### 6.5.1 add_layer.py 增强：插入前缩放

这是方案 1 的核心脚本。`add_layer.py` 不只是“添加图层”，还负责在插入前对外部素材做尺寸处理。

```
用法:
  python scripts/add_layer.py banner.psd product.png --name "Product" --top 120 --left 300
  python scripts/add_layer.py banner.psd product.png --name "Product" --width 600
  python scripts/add_layer.py banner.psd product.png --name "Product" --height 500
  python scripts/add_layer.py banner.psd product.png --name "Product" --fit-contain 800x800
  python scripts/add_layer.py banner.psd product.png --name "Product" --fit-cover 800x800
  python scripts/add_layer.py banner.psd product.png --name "Product" --scale 0.5
  python scripts/add_layer.py banner.psd product.png --name "Product" --center
```

建议支持的参数语义：

- `--width N`：按目标宽度等比缩放
- `--height N`：按目标高度等比缩放
- `--scale 0.5`：按比例缩放
- `--fit-contain WxH`：完整放进盒子，不裁剪
- `--fit-cover WxH`：铺满盒子，必要时裁剪
- `--top / --left`：指定左上角位置
- `--center`：自动居中放置

推荐约束：

- 同一条命令只允许一种尺寸策略，避免歧义
- 默认保持宽高比
- 默认使用高质量重采样
- 输出中明确报告原尺寸、目标尺寸、最终位置

### 6.5.2 resample_layer.py — 像素图层重建式缩放

这是方案 2 的核心脚本，只对 `pixel` 图层开放。

```
用法:
  python scripts/resample_layer.py banner.psd "Body/Product" --scale 0.5
  python scripts/resample_layer.py banner.psd "Body/Product" --width 600
  python scripts/resample_layer.py banner.psd "Body/Product" --height 500
  python scripts/resample_layer.py banner.psd "Body/Product" --fit-contain 800x800
```

内部步骤：

1. 校验目标图层 `kind == "pixel"`
2. 提取图层图像
3. 根据参数计算目标尺寸
4. 用 Pillow 重采样
5. 记录原图层父组、顺序、可见性、不透明度、混合模式
6. 删除原图层
7. 创建新像素图层并插回原位置
8. 恢复可恢复的基础属性

脚本输出应明确提示：

- 这是“重建式缩放”
- 哪些属性已恢复
- 哪些高级属性可能丢失

### 6.6 其他脚本（简要）

| 脚本 | 用法示例 |
|------|---------|
| `rename.py` | `python scripts/rename.py banner.psd "Layer 1" "Logo"` |
| `reorder.py` | `python scripts/reorder.py banner.psd "Logo" --up` / `--down` / `--to-index 0` |
| `move_layer.py` | `python scripts/move_layer.py banner.psd "Logo" --to-group "Header"` |
| `remove_layer.py` | `python scripts/remove_layer.py banner.psd "Header/Subtitle"` |
| `add_layer.py` | `python scripts/add_layer.py banner.psd product.png --name "Product" --width 600 --center` |
| `resample_layer.py` | `python scripts/resample_layer.py banner.psd "Body/Product" --scale 0.5` |
| `create_group.py` | `python scripts/create_group.py banner.psd "Footer" --layers "Copyright,Links"` |
| `export.py` | `python scripts/export.py banner.psd output.png` / `output.jpg --quality 90` |
| `export_layers.py` | `python scripts/export_layers.py banner.psd --output-dir ./layers/` |
| `extract_smart_object.py` | `python scripts/extract_smart_object.py banner.psd "Product Image" --output product.png` |
| `read_text.py` | `python scripts/read_text.py banner.psd "Header/Title"` |
| `save.py` | `python scripts/save.py banner.psd --output modified.psd` |

### 6.7 脚本设计原则

1. **每个脚本做一件事**，UNIX 哲学
2. **操作后自动保存**（除 preview/info/read_text 等只读操作外），保存路径默认覆盖原文件，可用 `--output` 指定另存
3. **图层路径用 "/" 分隔**，如 `"Header/Logo"` 表示 Header 组下的 Logo 图层
4. **所有输出是人类可读文本**，方便 Agent 解析
5. **失败时返回非零 exit code + 错误信息**，Agent 可据此重试
6. **预览图统一存到 `.tmp/` 目录**，Agent 可以直接 read 查看

---

## 七、AGENTS.md 设计

```markdown
# NL-PSD Agent

你是一个 PSD/PSB 文件编辑助手。用户通过自然语言描述需求，
你通过执行 Python 脚本来操作 PSD 文件。

## 你的能力

你可以：
- 打开和查看 PSD/PSB 文件结构
- **看到**文件的视觉效果（通过 preview.py 导出图片后查看）
- 切换图层可见性、调整不透明度、更改混合模式
- 重命名、删除、移动、重新排序图层
- 从图片添加新像素图层
- 在插入外部图片前先做缩放、contain / cover、居中放置
- 对普通像素图层执行重建式缩放
- 创建和管理图层组
- 读取文字图层内容（但不能修改文字）
- 导出为 PNG/JPG
- 保存修改后的 PSD 文件

你不能：
- 修改文字图层的内容（psd-tools 限制）
- 编辑形状图层或智能对象
- 添加/修改图层样式（投影、描边等）
- 应用调整图层效果
- 对任意图层进行 Photoshop 式原生变换（移动位置、缩放、旋转）
- 保证文字图层、形状图层、智能对象在缩放后仍保持原语义

## 工作流程

### 第一步：了解文件
用户提供 PSD 文件路径后，必须先执行：
1. `python scripts/info.py <文件>` — 获取图层结构
2. `python scripts/preview.py <文件>` — 生成预览图到 .tmp/preview.png
3. 读取 .tmp/preview.png 查看文件的视觉效果
4. 用自然语言向用户描述文件内容

### 第二步：执行操作
根据用户需求，调用对应的脚本。操作后：
1. 再次执行 `python scripts/preview.py <文件>` 生成新预览
2. 读取新预览图，确认操作效果
3. 向用户报告结果

### 第三步：保存
- 脚本默认会自动保存到原文件
- 如果用户要另存为，使用 `--output` 参数
- 重要操作前建议用户备份原文件

## 脚本使用参考

所有脚本在 `scripts/` 目录下，用法：

| 脚本 | 功能 | 示例 |
|------|------|------|
| info.py | 查看 PSD 信息 | `python scripts/info.py banner.psd` |
| preview.py | 生成预览图 | `python scripts/preview.py banner.psd` |
| visibility.py | 切换图层可见性 | `python scripts/visibility.py banner.psd "Logo" --hide` |
| opacity.py | 设置不透明度 | `python scripts/opacity.py banner.psd "Logo" 128` |
| blend_mode.py | 设置混合模式 | `python scripts/blend_mode.py banner.psd "Logo" screen` |
| rename.py | 重命名图层 | `python scripts/rename.py banner.psd "Layer 1" "Logo"` |
| reorder.py | 图层排序 | `python scripts/reorder.py banner.psd "Logo" --up` |
| move_layer.py | 移动图层到组 | `python scripts/move_layer.py banner.psd "Logo" --to-group "Header"` |
| remove_layer.py | 删除图层 | `python scripts/remove_layer.py banner.psd "Subtitle"` |
| add_layer.py | 添加图层 | `python scripts/add_layer.py banner.psd logo.png --name "Logo"` |
| resample_layer.py | 像素图层重建式缩放 | `python scripts/resample_layer.py banner.psd "Product" --scale 0.5` |
| create_group.py | 创建组 | `python scripts/create_group.py banner.psd "Footer"` |
| export.py | 导出图片 | `python scripts/export.py banner.psd output.png` |
| export_layers.py | 批量导出图层 | `python scripts/export_layers.py banner.psd` |
| read_text.py | 读取文字 | `python scripts/read_text.py banner.psd "Title"` |

## 图层路径规则

- 用 "/" 分隔组和图层：`"Header/Logo"` = Header 组下的 Logo
- 多层嵌套：`"Header/Sub Group/Logo"`
- 顶层图层直接用名称：`"Background"`
- 图层名区分大小写，中文图层名原样使用

## 注意事项

- **操作前先 info.py + preview.py**，不要凭猜测操作
- 不确定图层名时，先查看 info.py 输出
- 预览图保存在 .tmp/ 目录，可直接读取查看
- 对 PSD 文件的修改是破坏性的，重要文件操作前提醒用户备份
- 缩放需求默认优先走“插入前缩放”，而不是“重建式缩放”
- 只有确认目标层是 `pixel` 图层时，才允许执行 `resample_layer.py`
- 如果脚本报错，读取错误信息，分析原因后重试
- 一次只做一个操作，确认成功后再继续下一个
```

---

## 八、SKILL.md 设计

```markdown
---
name: psd-editor
description: |
  自然语言编辑 PSD/PSB 文件。当用户想要打开、查看、修改、导出 PSD 文件时激活。
  通过 psd-tools Python 库和预置脚本进行操作，支持图层管理、可见性、
  不透明度、混合模式等属性编辑、外部图片插入前缩放，以及像素图层的
  重建式缩放与文件导出。
---

## 激活条件

当用户提到以下关键词时激活：
- PSD、PSB、Photoshop
- 图层、图层组
- 打开/编辑/修改/导出 设计文件

## 环境要求

确保 Python 依赖已安装：
```bash
pip install psd-tools Pillow
```

## 核心工作流

### 1. 打开文件并了解内容
```bash
python scripts/info.py <文件路径>
python scripts/preview.py <文件路径>
# 然后读取 .tmp/preview.png 查看视觉效果
```

### 2. 执行编辑操作
根据用户需求调用对应脚本（详见 AGENTS.md 的脚本表）。

### 3. 验证结果
每次操作后重新生成预览图并查看，确认操作正确。

### 4. 保存
脚本默认自动保存。如需另存，使用 `--output` 参数。

## 能力边界

✅ 可以：图层显隐、不透明度、混合模式、重命名、排序、删除、
          添加像素图层、插入前缩放、像素图层重建式缩放、
          创建组、导出 PNG/JPG、读取文字内容

❌ 不能：修改文字内容、编辑形状/智能对象、图层样式、
          调整图层、任意图层的原生变换（移动/缩放/旋转）

遇到不支持的操作时，坦诚告知用户限制，并建议替代方案（如用 Photoshop 手动操作）。
```

---

## 九、使用方式

### 9.1 一次性安装

```powershell
cd D:\code\playground\nl-psd-agent
pip install -r requirements.txt
```

### 9.2 日常使用

```powershell
cd D:\code\playground\nl-psd-agent
codex
```

然后直接对话：

```
You: 打开 D:\designs\banner.psd，告诉我里面有什么

Agent: [执行 info.py + preview.py]
       [读取预览图]
       
       这是一个 1920×1080 的横幅设计...
       （图层结构 + 视觉描述）

You: 把 Background 图层隐藏

Agent: [执行 visibility.py ... --hide]
       [执行 preview.py 重新预览]
       [读取新预览图]
       
       已隐藏 Background 图层，现在背景变成透明了。

You: 导出为 PNG

Agent: [执行 export.py ... output.png]
       
       已导出到 output.png (1920×1080, 透明背景)
```

### 9.3 进阶用法

```
You: 帮我把这个 PSD 里所有图层都导出为单独的 PNG

Agent: [执行 export_layers.py]
       已导出 15 个图层到 ./layers/ 目录：
       - Header_Logo.png
       - Header_Title.png
       ...

You: 我有一张新的 logo.png，替换掉原来的 Logo 图层

Agent: [执行 remove_layer.py 删除旧 Logo]
       [执行 add_layer.py 添加新 Logo]
       [执行 preview.py 预览]
       
       已替换 Logo 图层。新 Logo 已添加到 Header 组中。

You: 插入 product.png，宽度缩到 620px，放在画布中央偏下

Agent: [执行 add_layer.py ... --width 620 --center]
       [执行 preview.py 预览]
       
       已插入商品图，原始尺寸 1600×1600，现已等比缩放到 620×620，
       并放置到画布中央偏下区域。

You: 把 Body/Product 图层再缩小到 80%

Agent: [检查该层是否为 pixel]
       [执行 resample_layer.py ... --scale 0.8]
       [执行 preview.py 预览]
       
       已按重建式缩放将 Product 图层缩小到 80%。
       图层名称、可见性和混合模式已恢复；高级元数据可能有损失。

You: 帮我看看 Title 图层用的什么字体、什么颜色

Agent: [执行 read_text.py]
       
       Title 图层文字信息：
       - 内容: "Summer Sale"
       - 字体: Helvetica Bold
       - 字号: 72px
       - 颜色: #FFFFFF (白色)
       - 对齐: 居中
```

---

## 十、requirements.txt

```
psd-tools>=1.14.0
Pillow>=10.0.0
```

可选（增强合成效果）：
```
psd-tools[composite]>=1.14.0
# 包含 aggdraw, scipy, scikit-image
# 用于矢量渲染、渐变填充、图层效果
```

---

## 十一、实施路线

### Phase 0: 环境验证（半天）

- [ ] 安装 psd-tools，验证基本读取/写入
- [ ] 测试 composite 导出效果
- [ ] 测试 PSB 文件支持
- [ ] 确认 Codex 能读取导出的 PNG 图片（视觉能力验证）
- [ ] 验证 Pillow 缩放后插入像素图层的可用性
- [ ] 验证像素图层重建式缩放后的保存与复合结果

### Phase 1: 核心脚本 + Agent 配置（1-2 天）

- [ ] 实现 `info.py` + `preview.py`（最重要的两个脚本）
- [ ] 实现 `visibility.py` + `opacity.py` + `blend_mode.py`
- [ ] 实现增强版 `add_layer.py`（支持 width / height / scale / contain / cover）
- [ ] 定义尺寸策略与定位策略（left/top/center）
- [ ] 编写 `AGENTS.md`
- [ ] 端到端测试：Codex 打开 PSD → 查看 → 修改 → 预览

### Phase 2: 完整脚本集（1-2 天）

- [ ] 实现所有剩余脚本
- [ ] 实现 `resample_layer.py`，并限制仅对 `pixel` 图层生效
- [ ] 为“插入前缩放”和“重建式缩放”补充 few-shot 示例
- [ ] 编写 `SKILL.md`
- [ ] 编写 `README.md`
- [ ] 多个 PSD/PSB 文件测试

### Phase 3: 优化体验（持续）

- [ ] 优化 AGENTS.md 中的 few-shot 示例
- [ ] 处理边缘情况（中文图层名、深层嵌套组等）
- [ ] 大文件性能优化（预览图缩放、图层树截断）
- [ ] 考虑添加"撤销"机制（操作前自动备份）
- [ ] 评估重建式缩放对 mask / clip / blend / layer order 的影响并补充限制说明
- [ ] 如缩放需求越来越重，评估是否引入 Photopea 作为 transform 补充引擎

---

## 十二、与 v4 的关系

v5 **不是** v4 的替代品，而是另一条路径：

| 维度 | v4 (Photopea) | v5 (psd-tools) |
|------|--------------|----------------|
| 定位 | 完整 PSD 编辑器 | 轻量图层管理工具 |
| 文字编辑 | ✅ 支持 | ❌ 不支持 |
| 变换操作 | ✅ 支持 | ⚠️ 仅支持两种替代路径：插入前缩放、像素图层重建式缩放 |
| 视觉反馈 | 需要浏览器 + Playwright | 原生支持（composite → 视觉模型） |
| 启动复杂度 | 高（3+ 进程） | 低（1 个终端） |
| 开发量 | 2-3 天（含 Bridge） | 1-2 天（纯脚本） |
| 适合场景 | 需要完整编辑能力 | 图层管理 + 属性调整 + 文件导出 |

**推荐策略**：先用 v5 快速出一个可用的 Agent，体验"自然语言操作 PSD"的核心价值。如果后续需要文字编辑等更丰富的能力，再引入 v4 的 Photopea 方案作为补充。

---

## 十三、开放讨论点

### 1. 脚本粒度问题

当前设计是"一个脚本一个功能"。另一种思路是做一个**统一 CLI 入口**：

```bash
python psd_tool.py info banner.psd
python psd_tool.py preview banner.psd
python psd_tool.py set-visibility banner.psd "Logo" false
python psd_tool.py set-opacity banner.psd "Logo" 128
```

哪种对 Codex 更友好？分开的脚本文件名更直观，但统一入口减少文件数量。

### 2. 自动备份策略

每次修改前自动复制一份 `banner.psd.bak`？还是交给用户管理？
或者用 git 管理 PSD 文件的版本？

### 3. 图层路径 vs 索引

当图层名有重复时（很常见），用路径 `"Header/Logo"` 可能还不够唯一。
是否需要支持索引访问：`"#3"` 或 `"Header/#1"`？

### 4. 缩放策略默认值

既然 v5 现在支持两种“非原生缩放”路径，需要明确默认决策：

- 外部素材进入 PSD：默认走“插入前缩放”
- 已有图层：只有 `pixel` 图层允许“重建式缩放”
- 文字 / 形状 / 智能对象：默认拒绝，并解释原因
- 默认保持等比缩放
- 默认优先 `contain`，减少误裁剪风险

### 5. 预览图大小控制

大尺寸 PSD（如 4000×3000）的 composite 可能很慢且图片很大。
是否默认缩放到 max 1024px？还是保持原始尺寸？

### 6. 是否需要 MCP？

当前方案完全不需要 MCP —— Codex 直接执行 Python 脚本。
这是优点（简单），也是限制（如果以后想接入 Claude Code 或其他 Agent，
MCP 会是更标准的接口）。后续如果需要，可以把脚本包装为 MCP Server。
