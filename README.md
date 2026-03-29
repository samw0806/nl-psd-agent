# NL-PSD Agent

自然语言驱动的 PSD/PSB 文件编辑工具。通过 AI Agent（Codex CLI / Claude Code）理解自然语言指令，执行 Python 脚本操作 PSD 文件，并通过视觉模型查看合成效果。

> **当前方案**: v5 — psd-tools + Codex 纯 CLI 方案（详见 plans/v5-psd-tools-codex.md）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 用 Codex CLI
cd /path/to/nl-psd-agent && codex

# 用 Claude Code
cd /path/to/nl-psd-agent && claude
```

然后直接对话：
```
你: 打开 banner.psd，告诉我里面有什么
你: 把 Background 图层隐藏掉
你: 插入 logo.png，宽度缩到 400px，放在画布中央
你: 导出为 PNG
```

## 支持的操作

| 类别 | 操作 |
|------|------|
| 查看 | 文件信息、图层树、合成预览、单图层预览 |
| 属性 | 可见性、不透明度（0-255 或百分比）、混合模式 |
| 结构 | 重命名、删除、移动到组、上移/下移 |
| 新建 | 从外部图片插入像素图层（支持等比缩放/contain/cover/居中） |
| 缩放 | 对已有像素图层做重建式缩放 |
| 组管理 | 创建组、将现有图层归入组 |
| 文字 | 读取文字内容、字体、字号、颜色（只读） |
| 导出 | PNG、JPG、批量导出所有图层、提取智能对象 |
| 保存 | 覆盖保存、另存为 |

## 不支持的操作

- 修改文字图层内容（psd-tools 硬限制）
- 编辑形状图层/智能对象
- 图层样式（投影、描边、发光等）
- 调整图层效果
- Photoshop 式原生变换（任意图层的移动/旋转）

## 项目结构

```
nl-psd-agent/
├── AGENTS.md              # Codex 项目指引
├── CLAUDE.md              # Claude Code 项目指引
├── requirements.txt       # Python 依赖
├── scripts/               # Python CLI 脚本（17 个）
│   ├── _utils.py          # 公共工具（图层路径解析等）
│   ├── info.py            # 查看文件信息 + 图层树
│   ├── preview.py         # 合成预览图 → .tmp/preview.png
│   ├── visibility.py      # 切换图层可见性
│   ├── opacity.py         # 设置不透明度
│   ├── blend_mode.py      # 设置混合模式
│   ├── rename.py          # 重命名图层
│   ├── reorder.py         # 图层排序
│   ├── move_layer.py      # 移动图层到组
│   ├── remove_layer.py    # 删除图层
│   ├── add_layer.py       # 插入外部图片图层（含缩放）
│   ├── resample_layer.py  # 像素图层重建式缩放
│   ├── create_group.py    # 创建图层组
│   ├── export.py          # 导出为 PNG/JPG
│   ├── export_layers.py   # 批量导出所有图层
│   ├── extract_smart_object.py  # 提取智能对象内容
│   ├── read_text.py       # 读取文字图层内容
│   └── save.py            # 保存文件
├── .agents/               # Codex Skills
│   └── skills/psd-editor/SKILL.md
├── .tmp/                  # 临时文件（预览图，已加入 .gitignore）
├── examples/              # 示例 PSD 文件
└── plans/                 # 架构设计文档（v1-v5）
```

## 脚本直接使用

```bash
python scripts/info.py banner.psd
python scripts/preview.py banner.psd
python scripts/visibility.py banner.psd "Header/Logo" --hide
python scripts/opacity.py banner.psd "Logo" 50%
python scripts/add_layer.py banner.psd product.png --name "Product" --width 600 --center
python scripts/export.py banner.psd output.jpg --quality 90
```

## 技术架构

```
用户 (自然语言) → AI Agent (Codex/Claude) → Python 脚本 → psd-tools + Pillow → PSD 文件
                                                ↑
                                          .tmp/preview.png (视觉反馈)
```

- **psd-tools** ≥1.14.0：PSD/PSB 读写引擎（MIT 协议）
- **Pillow** ≥10.0.0：图像处理
- 每个脚本独立完成一个操作（UNIX 哲学）
- Agent 直接通过 shell 执行脚本，无中间层、无浏览器依赖

## 历史设计文档

| 文档 | 说明 |
|------|------|
| plans/v1-architecture.md | 顶层架构设计（选型分析） |
| plans/v2-architecture.md | 详细架构设计（Photopea + MCP 方案） |
| plans/v3-frontend-design.md | 前端 UI/UX 设计 |
| plans/v4-codex-implementation-discussion.md | Codex 实施讨论 |
| plans/v5-psd-tools-codex.md | **当前方案**：psd-tools + 纯 CLI |
