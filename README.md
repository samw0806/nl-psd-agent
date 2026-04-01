# NL-PSD Agent

自然语言驱动的 PSD/PSB 文件编辑工具。通过 AI Agent 理解自然语言指令，执行 Python 脚本操作 PSD 文件，并实时预览合成效果。

支持三种使用方式：**Web 应用**、**Codex CLI**、**Claude Code**。

> **当前版本**: v6 — FastAPI + React Web 应用 + 完整评测体系

---

## 环境准备

### 1. 配置 API 密钥

项目使用 `.env` 文件管理配置，**无需每次手动 export**：

```bash
cp .env.example .env
```

编辑 `.env`，填入你的配置：

```ini
# 必填：Anthropic API 密钥
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx

# 可选：第三方代理或私有部署时填写
ANTHROPIC_BASE_URL=https://your-proxy.example.com
```

`.env` 已加入 `.gitignore`，不会被提交。

### 2. 创建虚拟环境

```bash
cd /path/to/nl-psd-agent

# 创建 venv（项目根目录，后端脚本执行依赖此路径）
python3 -m venv .venv

# 激活
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt          # 脚本层依赖
pip install -r backend/requirements.txt  # Web 后端依赖
```

> **注意**：venv 必须在项目根目录的 `.venv/`，后端代码硬编码了此路径来执行脚本。

---

## 快速开始

### 方式一：Web 应用（推荐）

```bash
# 确保已完成「环境准备」

# 启动后端（终端 1）
cd /path/to/nl-psd-agent
source .venv/bin/activate
uvicorn backend.main:app --reload
# API 服务: http://localhost:8000

# 启动前端（终端 2）
cd frontend
npm install && npm run dev
# 前端页面: http://localhost:5173
```

浏览器打开 `http://localhost:5173`，上传 PSD 文件后直接与 Agent 对话。

### 方式二：CLI（Codex / Claude Code）

```bash
source .venv/bin/activate

# 使用 Codex CLI
cd /path/to/nl-psd-agent && codex

# 使用 Claude Code
cd /path/to/nl-psd-agent && claude
```

然后直接对话：

```
你: 打开 banner.psd，告诉我里面有什么
你: 把 Background 图层隐藏掉
你: 插入 logo.png，宽度缩到 400px，放在画布中央
你: 导出为 PNG
```

### 方式三：直接调用脚本

```bash
source .venv/bin/activate

python scripts/info.py banner.psd
python scripts/preview.py banner.psd
python scripts/visibility.py banner.psd "Header/Logo" --hide
python scripts/opacity.py banner.psd "Logo" 50%
python scripts/add_layer.py banner.psd product.png --name "Product" --width 600 --center
python scripts/position_layer.py banner.psd "Body/ProductShot" --dx 40 --dy 20
python scripts/export.py banner.psd output.jpg --quality 90
```

---

## 支持的操作

| 类别 | 操作 |
|------|------|
| 查看 | 文件信息、图层树、合成预览、单图层预览 |
| 属性 | 可见性、不透明度（0-255 或百分比）、混合模式 |
| 结构 | 重命名、删除、移动到组、上移/下移、非组图层坐标移动 |
| 新建 | 从外部图片插入像素图层（支持等比缩放 / contain / cover / 居中） |
| 缩放 | 对已有像素图层做重建式缩放 |
| 栅格化 | 将 Smart Object / Shape / Type 图层转为像素图层（不可逆，执行前确认） |
| 组管理 | 创建组、将现有图层归入组 |
| 文字 | 读取文字内容、字体、字号、颜色（**只读**） |
| 导出 | PNG、JPG、批量导出所有图层、提取智能对象 |
| 保存 | 覆盖保存、另存为 |

## 不支持的操作

> 以下为 psd-tools 硬限制，无法绕过，建议在 Photoshop 中手动处理。

- 修改文字图层内容
- 编辑形状图层或智能对象
- 图层样式（投影、描边、发光等）
- 调整图层效果
- Photoshop 式原生变换（任意图层的自由旋转）
- 组图层整体坐标移动（当前只支持非组图层坐标移动）

---

## 技术架构

### Web 应用架构

```
用户（浏览器对话）
       ↓
  React 前端
  (SSE 流式接收)
       ↓
  FastAPI 后端
  (加载 .env 配置)
       ↓
  Claude Tool Use Agent
  (backend/agent.py)
       ↓
  Python 脚本执行
  (scripts/*.py via .venv/bin/python)
       ↓
  psd-tools + Pillow → PSD 文件
       ↓
  preview.png → 前端实时刷新
```

### CLI 架构

```
用户（自然语言）→ AI Agent（Codex / Claude）→ Python 脚本 → psd-tools + Pillow → PSD 文件
                                                    ↑
                                              .tmp/preview.png（视觉反馈）
```

### 关键设计

- **20 个独立 Python 脚本**：UNIX 单一职责哲学，每脚本完成一个操作
- **Session + 快照**：Web 模式下每次修改前自动拍快照，支持无限 Undo/Redo
- **SSE 流式输出**：Agent 思考过程和工具调用状态实时推送到前端
- **图层路径规则**：用 `/` 分隔层级，如 `"Header/Logo"` 表示 Header 组下的 Logo

---

## 项目结构

```
nl-psd-agent/
├── .env.example           # 环境变量模板（复制为 .env 后填写）
├── .env                   # 本地配置（含密钥，已 gitignore）
├── CLAUDE.md              # Claude Code 项目指引（能力边界 + 工作流）
├── AGENTS.md              # Codex 项目指引
├── requirements.txt       # Python 依赖（脚本层）
│
├── scripts/               # 20 个 Python CLI 脚本（核心）
│   ├── _utils.py          # 公共工具（图层路径解析、错误处理）
│   ├── info.py            # 查看文件信息 + 图层树
│   ├── preview.py         # 合成预览 → .tmp/preview.png
│   ├── visibility.py      # 切换图层可见性
│   ├── opacity.py         # 设置不透明度
│   ├── blend_mode.py      # 设置混合模式
│   ├── rename.py          # 重命名图层
│   ├── reorder.py         # 图层排序（上移/下移/指定索引）
│   ├── move_layer.py      # 移动图层到组
│   ├── position_layer.py  # 调整非组图层坐标
│   ├── remove_layer.py    # 删除图层
│   ├── add_layer.py       # 插入外部图片图层（含缩放）
│   ├── resample_layer.py  # 像素图层重建式缩放
│   ├── rasterize_layer.py # 栅格化 Smart/Shape/Type → Pixel
│   ├── create_group.py    # 创建图层组
│   ├── export.py          # 导出为 PNG/JPG
│   ├── export_layers.py   # 批量导出所有图层
│   ├── extract_smart_object.py  # 提取智能对象内容
│   ├── read_text.py       # 读取文字图层内容
│   └── save.py            # 保存文件
│
├── backend/               # FastAPI 后端
│   ├── main.py            # FastAPI 入口 + 路由定义（启动时加载 .env）
│   ├── agent.py           # Claude Tool Use Agent（SSE 流式）
│   ├── session.py         # Session 管理 + 版本快照 + Undo/Redo
│   ├── tools.py           # 脚本包装 + Tool 定义
│   └── requirements.txt   # 后端依赖
│
├── frontend/              # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx        # 主应用（左侧预览 + 右侧聊天布局）
│   │   ├── api/client.ts  # API 调用封装
│   │   ├── hooks/
│   │   │   ├── useSession.ts   # 状态管理
│   │   │   └── useSSE.ts       # SSE 流处理
│   │   └── components/
│   │       ├── PreviewCanvas.tsx    # 预览画布（支持缩放平移）
│   │       ├── ChatPanel.tsx        # 聊天面板
│   │       ├── ToolCallStatus.tsx   # 工具执行状态
│   │       └── Toolbar.tsx          # Undo/Redo/导出工具栏
│   └── package.json
│
├── eval/                  # 评测框架（v6 新增）
│   ├── runner.py          # 评测执行器
│   ├── generate_fixtures.py  # 生成合成测试 PSD
│   ├── cases/             # 测试用例（YAML）
│   │   ├── script/        # 脚本层用例
│   │   └── agent/         # Agent 层用例
│   ├── fixtures/          # 合成测试 PSD
│   └── results/           # 测试结果输出
│
├── tests/                 # 回归测试
├── .agents/               # Codex Skills
├── .tmp/                  # 临时文件（预览图，已 gitignore）
├── .venv/                 # Python 虚拟环境（已 gitignore）
├── examples/              # 示例 PSD/PSB 文件（大文件，已 gitignore）
└── plans/                 # 架构设计文档
```

---

## API 参考（Web 模式）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 创建新 Session |
| GET | `/api/sessions/{sid}` | 获取 Session 状态 |
| POST | `/api/sessions/{sid}/upload` | 上传 PSD 文件 |
| GET | `/api/sessions/{sid}/preview` | 获取当前预览图 |
| GET | `/api/sessions/{sid}/chat?message=...` | 与 Agent 对话（SSE 流式） |
| POST | `/api/sessions/{sid}/undo` | 撤销上一步操作 |
| POST | `/api/sessions/{sid}/redo` | 重做 |
| POST | `/api/sessions/{sid}/export?format=png\|jpg` | 导出为图片并下载 |
| DELETE | `/api/sessions/{sid}` | 删除 Session |

### SSE 事件格式

```json
{ "type": "text",      "content": "正在处理..." }
{ "type": "tool_call", "tool": "get_psd_info", "status": "running", "tool_use_id": "xxx" }
{ "type": "tool_call", "tool": "get_psd_info", "status": "done",    "output": "...", "tool_use_id": "xxx" }
{ "type": "preview",   "url": "/api/sessions/{sid}/preview?t=1234567890" }
{ "type": "done" }
{ "type": "error",     "message": "错误信息" }
```

---

## 依赖

### Python（脚本层）

```
psd-tools>=1.14.0     # PSD/PSB 读写引擎（MIT 协议）
Pillow>=10.0.0        # 图像处理
scikit-image>=0.21.0  # 增强合成效果
aggdraw>=1.3.11       # 矢量形状渲染
```

### Python（Web 后端，`backend/requirements.txt`）

```
fastapi>=0.111.0           # Web 框架
uvicorn[standard]>=0.29.0  # ASGI 服务器
anthropic>=0.28.0          # Claude API SDK
aiofiles>=23.2.1           # 异步文件操作
python-multipart>=0.0.9    # 表单数据解析
python-dotenv>=1.0.0       # 加载 .env 配置
```

### 前端

```
React 18.3 + TypeScript
Vite 5.4
Tailwind CSS 3.4
react-zoom-pan-pinch 3.7  # 预览画布缩放
```

---

## 设计文档

| 文档 | 说明 |
|------|------|
| plans/system-design.md | v5+ 系统整体设计 |
| plans/v6-evaluation-and-benchmark.md | v6 评测体系规划 |
| plans/v4-codex-implementation-discussion.md | Codex CLI 实施讨论 |
| plans/v1~v3 | 早期架构探索（Photopea / MCP 方案等） |
