"""
agent.py — Claude Tool Use Agent，通过 SSE 流式输出事件
"""
import json
import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator

import anthropic

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from backend.session import (
    get_current_psd,
    get_preview_path,
    snapshot_before_edit,
    get_state,
    get_conversation_history,
    save_conversation_history,
    undo,
)
from backend.tools import TOOL_DEFINITIONS, execute_tool, READ_ONLY_TOOLS

CLAUDE_MD = Path(__file__).parent.parent / "CLAUDE.md"

SYSTEM_PROMPT_SUFFIX = """
## Web 模式说明

你现在运行在 Web 应用中。用户通过浏览器与你对话，PSD 文件已上传到服务器。
- psd_path 始终由系统提供，不需要用户输入
- 每次执行修改操作后，务必调用 preview_psd 刷新预览
- 不要提示用户激活虚拟环境，脚本已由后端自动调用
"""


def _get_system_prompt() -> str:
    if CLAUDE_MD.exists():
        return CLAUDE_MD.read_text(encoding="utf-8") + "\n" + SYSTEM_PROMPT_SUFFIX
    return "你是 PSD 编辑助手。" + SYSTEM_PROMPT_SUFFIX


def _sse(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


async def run_agent(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """运行 Agent，yield SSE 格式的字符串"""
    try:
        client = anthropic.Anthropic()
        system_prompt = _get_system_prompt()
        psd_path = str(get_current_psd(session_id))
        preview_path = get_preview_path(session_id)

        # 加载对话历史
        messages = get_conversation_history(session_id)

        # 注入 psd_path 上下文
        augmented_message = f"[当前文件: {psd_path}]\n\n{user_message}"
        messages.append({"role": "user", "content": augmented_message})

        loop = asyncio.get_event_loop()

        while True:
            # 收集完整响应
            full_text = ""
            tool_calls = []
            stop_reason = None
            stream = None
            final_message = None

            try:
                with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=4096,
                    system=system_prompt,
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                ) as stream:
                    current_tool_index = None
                    current_tool_name = None
                    current_tool_input_str = ""

                    for event in stream:
                        if event.type == "content_block_start":
                            block = event.content_block
                            if block.type == "text":
                                pass
                            elif block.type == "tool_use":
                                current_tool_index = event.index
                                current_tool_name = block.name
                                current_tool_input_str = ""
                                yield _sse("tool_call", {
                                    "tool": block.name,
                                    "tool_use_id": block.id,
                                    "status": "running",
                                    "args": {}
                                })

                        elif event.type == "content_block_delta":
                            delta = event.delta
                            if delta.type == "text_delta":
                                full_text += delta.text
                                yield _sse("text", {"content": delta.text})
                            elif delta.type == "input_json_delta":
                                current_tool_input_str += delta.partial_json

                        elif event.type == "content_block_stop":
                            if current_tool_name and current_tool_input_str is not None:
                                try:
                                    tool_input = json.loads(current_tool_input_str) if current_tool_input_str else {}
                                except json.JSONDecodeError:
                                    tool_input = {}
                                tool_calls.append({
                                    "name": current_tool_name,
                                    "input": tool_input,
                                    "index": current_tool_index,
                                })
                                current_tool_name = None
                                current_tool_input_str = ""

                        elif event.type == "message_delta":
                            if hasattr(event.delta, "stop_reason"):
                                stop_reason = event.delta.stop_reason

                    # 获取最终消息（在 with 块内）
                    final_message = stream.get_final_message()

            except Exception as e:
                logger.error(f"Claude API 调用异常: {str(e)}", exc_info=True)
                yield _sse("error", {"message": f"API 调用失败: {str(e)}"})
                return

            # 构建 assistant 消息内容（手动序列化，避免 SDK 内部字段污染）
            if final_message is None:
                logger.error("未能获取最终消息")
                yield _sse("error", {"message": "未能获取 API 响应"})
                return

            serialized_content = []
            for block in final_message.content:
                if block.type == "text":
                    serialized_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    serialized_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
            messages.append({"role": "assistant", "content": serialized_content})

            if stop_reason != "tool_use" or not tool_calls:
                break

            # 执行工具
            tool_results = []
            # 建立 tool_use_id 映射（按工具名 → id，保留顺序）
            tool_use_id_map: dict[str, list[str]] = {}
            for block in serialized_content:
                if block["type"] == "tool_use":
                    tool_use_id_map.setdefault(block["name"], []).append(block["id"])
            tool_use_counters: dict[str, int] = {}

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_input = tc["input"]

                try:
                    logger.info(f"执行工具: {tool_name}, 参数: {tool_input}")

                    # 修改操作前拍快照
                    if tool_name not in READ_ONLY_TOOLS:
                        await loop.run_in_executor(None, snapshot_before_edit, session_id)

                    # 执行工具（在线程池中运行同步代码）
                    output = await loop.run_in_executor(None, execute_tool, tool_name, tool_input)

                    logger.info(f"工具执行完成: {tool_name}, 输出长度: {len(output)}")

                    # 检查是否失败，如果失败则自动回滚
                    if tool_name not in READ_ONLY_TOOLS and ("错误:" in output or "错误：" in output):
                        # 自动回滚到上一个版本
                        undo_success = await loop.run_in_executor(None, undo, session_id)
                        if undo_success:
                            output += "\n\n⚠️ 操作失败，已自动回滚到操作前的状态。"
                        else:
                            output += "\n\n⚠️ 操作失败，但无法自动回滚（可能没有可用的历史版本）。"

                except Exception as e:
                    logger.error(f"工具执行异常: {tool_name}, 错误: {str(e)}", exc_info=True)
                    output = f"错误: 工具执行失败 - {str(e)}"

                    # 如果是修改操作，尝试回滚
                    if tool_name not in READ_ONLY_TOOLS:
                        try:
                            undo_success = await loop.run_in_executor(None, undo, session_id)
                            if undo_success:
                                output += "\n\n⚠️ 已自动回滚到操作前的状态。"
                        except Exception as undo_error:
                            logger.error(f"回滚失败: {str(undo_error)}")

                # 找到对应的 tool_use block id（按顺序匹配同名工具）
                idx = tool_use_counters.get(tool_name, 0)
                ids = tool_use_id_map.get(tool_name, [])
                tool_use_id = ids[idx] if idx < len(ids) else None
                tool_use_counters[tool_name] = idx + 1

                yield _sse("tool_call", {
                    "tool": tool_name,
                    "tool_use_id": tool_use_id,
                    "status": "done",
                    "output": output[:500],  # 截断避免过长
                    "args": tool_input,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": output,
                })

                # preview_psd 执行后通知前端刷新
                if tool_name == "preview_psd" and preview_path.exists():
                    import time
                    yield _sse("preview", {
                        "url": f"/api/sessions/{session_id}/preview?t={int(time.time() * 1000)}"
                    })

            messages.append({"role": "user", "content": tool_results})

        # 保存对话历史
        save_conversation_history(session_id, messages)

        yield _sse("done", {})

    except Exception as e:
        logger.error(f"Agent 运行异常: {str(e)}", exc_info=True)
        yield _sse("error", {"message": f"系统错误: {str(e)}"})
        yield _sse("done", {})
