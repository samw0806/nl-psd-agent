// hooks/useSSE.ts — SSE 流式接收

import { useCallback, useRef } from 'react'
import { chatUrl } from '../api/client'
import { SessionStore, ToolCallEvent } from './useSession'

interface SSEEvent {
  type: 'text' | 'tool_call' | 'preview' | 'done' | 'error'
  content?: string
  tool?: string
  tool_use_id?: string
  status?: 'running' | 'done'
  args?: Record<string, unknown>
  output?: string
  url?: string
  message?: string
}

export function useSSE(store: SessionStore) {
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      if (!store.sessionId) return
      if (store.isStreaming) {
        abortRef.current?.abort()
      }

      // 添加用户消息
      store.appendMessage({ id: String(Date.now()), role: 'user', content: text })
      // 添加空的 assistant 消息（流式填充）
      const assistantId = String(Date.now() + 1)
      store.appendMessage({
        id: assistantId,
        role: 'assistant',
        content: '',
        toolCalls: [],
      })

      store.setStreaming(true)
      store.setError(null)

      const ctrl = new AbortController()
      abortRef.current = ctrl

      try {
        const res = await fetch(chatUrl(store.sessionId, text), {
          signal: ctrl.signal,
        })

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }

        const reader = res.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            try {
              const event: SSEEvent = JSON.parse(raw)
              handleEvent(event, store)
            } catch {
              // ignore parse errors
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') {
          store.setError(err.message)
        }
      } finally {
        store.setStreaming(false)
      }
    },
    [store]
  )

  return { sendMessage }
}

function handleEvent(event: SSEEvent, store: SessionStore) {
  switch (event.type) {
    case 'text':
      store.updateLastAssistantMessage((msg) => ({
        ...msg,
        content: msg.content + (event.content ?? ''),
      }))
      break

    case 'tool_call': {
      const tc: ToolCallEvent = {
        tool: event.tool!,
        tool_use_id: event.tool_use_id,
        status: event.status ?? 'running',
        args: event.args,
        output: event.output,
      }
      store.updateLastAssistantMessage((msg) => {
        const existing = msg.toolCalls ?? []
        // 找到同 id 的 running 条目，若存在则更新为 done
        const idx = existing.findIndex(
          (t) => t.tool_use_id === tc.tool_use_id && t.status === 'running'
        )
        if (idx !== -1) {
          const updated = [...existing]
          updated[idx] = tc
          return { ...msg, toolCalls: updated }
        }
        return { ...msg, toolCalls: [...existing, tc] }
      })
      break
    }

    case 'preview':
      if (event.url) {
        store.setPreview(event.url)
      }
      break

    case 'error':
      store.setError(event.message ?? 'Unknown error')
      break

    case 'done':
      break
  }
}
