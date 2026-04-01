# 对话历史功能测试指南

## 功能说明

现在 Agent 可以记住对话上下文了！每次对话都会保存到 session 中，下次对话时会自动加载历史。

## 实现的功能

### 后端
1. ✅ Session 中添加 `conversation_history` 字段
2. ✅ 提供 `get_conversation_history()` 和 `save_conversation_history()` 函数
3. ✅ Agent 在每次对话时加载历史，结束时保存历史
4. ✅ 新增 API 端点：
   - `POST /api/sessions/{sid}/clear-history` - 清空对话历史
   - `GET /api/sessions/{sid}/history` - 查看对话历史（调试用）

### 前端
1. ✅ 添加"清空"按钮到 ChatPanel 头部
2. ✅ 点击清空按钮会清空前端消息列表和后端历史
3. ✅ 有确认对话框防止误操作

## 测试步骤

### 1. 启动应用

```bash
# 终端 1：启动后端
cd /home/sam/code/nl-psd-agent
source .venv/bin/activate
uvicorn backend.main:app --reload

# 终端 2：启动前端（如果需要开发模式）
cd frontend
npm run dev
```

### 2. 基础对话上下文测试

1. 打开浏览器访问 `http://localhost:8000`
2. 上传一个 PSD 文件
3. 发送第一条消息：**"这个文件里有哪些图层？"**
   - Agent 会调用 `info.py` 列出图层
4. 发送第二条消息：**"把第一个图层隐藏"**
   - 注意：这里没有再说明是哪个文件
   - Agent 应该能记住之前的对话，知道要操作哪个图层
5. 发送第三条消息：**"刚才我让你隐藏的是哪个图层？"**
   - Agent 应该能回答出具体的图层名称

**预期结果**：Agent 能够正确回答第 3 步的问题，说明对话上下文已保持。

### 3. 清空历史测试

1. 在有对话历史的情况下，点击右上角的"清空"按钮
2. 确认对话框中点击"确定"
3. 前端的消息列表应该被清空
4. 发送新消息：**"刚才我们聊了什么？"**
   - Agent 应该回答不知道或说这是第一次对话

**预期结果**：清空后 Agent 不记得之前的对话。

### 4. 调试 API 测试

使用 curl 查看对话历史（需要替换 `{session_id}`）：

```bash
# 查看对话历史
curl http://localhost:8000/api/sessions/{session_id}/history | jq

# 清空对话历史
curl -X POST http://localhost:8000/api/sessions/{session_id}/clear-history
```

## 技术细节

### 对话历史格式

```json
{
  "conversation_history": [
    {
      "role": "user",
      "content": "[当前文件: /path/to/file.psd]\n\n这个文件里有哪些图层？"
    },
    {
      "role": "assistant",
      "content": [
        {"type": "text", "text": "让我查看一下..."},
        {"type": "tool_use", "id": "...", "name": "info_psd", "input": {...}}
      ]
    },
    {
      "role": "user",
      "content": [
        {"type": "tool_result", "tool_use_id": "...", "content": "..."}
      ]
    },
    {
      "role": "assistant",
      "content": [
        {"type": "text", "text": "这个文件包含以下图层：..."}
      ]
    },
    {
      "role": "user",
      "content": "[当前文件: /path/to/file.psd]\n\n把第一个图层隐藏"
    }
  ]
}
```

### 存储位置

对话历史保存在：`sessions/{session_id}/state.json` 的 `conversation_history` 字段中。

### 性能考虑

- 对话历史会随着对话增长而变大
- 目前没有限制历史长度
- 如果需要，可以后续添加：
  - 限制最大历史长度（如保留最近 20 轮）
  - 实现"总结压缩"机制
  - 自动清理过期 session

## 与 Claude Code CLI 的对比

| 特性 | Claude Code CLI | nl-psd-agent Web 版 |
|------|----------------|-------------------|
| 对话历史管理 | CLI 框架自动管理 | 手动实现（Session） |
| 存储位置 | `~/.claude/` | `sessions/{sid}/state.json` |
| 架构模型 | 长期运行进程 | 无状态 HTTP 请求 |
| 清空历史 | 重启 CLI | 点击"清空"按钮 |

## 故障排查

### Agent 还是不记得上下文

1. 检查后端日志，确认 `save_conversation_history` 被调用
2. 查看 `sessions/{sid}/state.json`，确认 `conversation_history` 字段存在且有内容
3. 使用调试 API 查看历史：`GET /api/sessions/{sid}/history`

### 清空按钮不工作

1. 检查浏览器控制台是否有错误
2. 确认 API 端点返回成功：`POST /api/sessions/{sid}/clear-history`
3. 检查前端 `clearMessages()` 是否被调用

## 后续优化建议

1. **历史长度限制**：添加配置项限制最大历史轮数
2. **总结压缩**：当历史过长时，自动总结旧对话
3. **导出历史**：允许用户导出对话历史为 JSON/Markdown
4. **搜索历史**：在前端添加搜索功能
5. **多会话管理**：允许用户创建多个独立的对话会话
