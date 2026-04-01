# NL-PSD Agent — System Design

## Overview

Web 应用将现有 CLI Python 脚本封装为 AI Agent 对话式 PSD 编辑器。用户通过右侧自然语言面板操作 PSD，左侧大面积区域实时渲染效果图。

## Architecture

```
Browser (React + Vite)
  │
  ├── GET/POST /api/*  ──→  FastAPI (uvicorn)
  │                              │
  │                              ├── session.py   (文件管理/版本)
  │                              ├── tools.py     (脚本包装)
  │                              └── agent.py     (Claude SSE Agent)
  │                                      │
  │                                      └── scripts/*.py  (PSD 操作)
  │
  └── GET /api/sessions/{id}/chat  ──→  SSE Stream
```

## Key Design Decisions

### 版本管理（快照策略）
每次调用修改脚本前，`session.py` 将 `current.psd` 复制为 `history/v{n}.psd`。
undo/redo 只需复制对应版本回 `current.psd`，然后重新生成 preview。

```
state.json:
{
  "version": 3,
  "undo_stack": [0, 1, 2],
  "redo_stack": []
}
```

### SSE 事件协议

```json
{ "type": "text",      "content": "好的..." }
{ "type": "tool_call", "tool": "visibility.py", "status": "running" }
{ "type": "tool_call", "tool": "visibility.py", "status": "done", "output": "..." }
{ "type": "preview",   "url": "/api/sessions/{id}/preview?t=12345" }
{ "type": "done" }
{ "type": "error",     "message": "..." }
```

### Tool Execution
- 只读工具（`get_psd_info`, `preview_psd`, `read_text`）：直接执行，不拍快照
- 修改工具：先 `snapshot_before_edit()`，再执行脚本，再 `preview_psd`

## Directory Structure (Runtime)

```
sessions/{uuid}/
  current.psd       — 当前工作文件
  state.json        — 版本栈
  history/
    v0.psd, v1.psd  — 历史版本
  .tmp/
    preview.png     — 最新预览图
    export.png/jpg  — 导出临时文件
```

## API Summary

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/sessions | 创建 Session |
| GET | /api/sessions/{id} | 获取状态 |
| POST | /api/sessions/{id}/upload | 上传 PSD |
| GET | /api/sessions/{id}/preview | 获取预览图 |
| POST | /api/sessions/{id}/undo | 撤销 |
| POST | /api/sessions/{id}/redo | 重做 |
| POST | /api/sessions/{id}/export | 导出 PNG/JPG |
| GET | /api/sessions/{id}/chat | SSE Agent 对话 |
| DELETE | /api/sessions/{id} | 删除 Session |

## Frontend State Flow

```
initSession() → POST /api/sessions → sessionId
uploadFile()  → POST /upload       → sessionState + previewVersion++
sendMessage() → GET /chat (SSE)    → stream text/tool_call/preview events
undo()/redo() → POST /undo|redo    → sessionState + previewVersion++
```
