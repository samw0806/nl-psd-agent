// components/ChatPanel.tsx — 右侧 Agent 对话面板
import { SessionStore } from '../hooks/useSession'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { useSSE } from '../hooks/useSSE'
import { clearHistory } from '../api/client'
import { useState } from 'react'

interface Props {
  store: SessionStore
}

export function ChatPanel({ store }: Props) {
  const { sendMessage } = useSSE(store)
  const { sessionState, error } = store
  const [isClearing, setIsClearing] = useState(false)

  const handleClearHistory = async () => {
    if (!store.sessionId) return
    if (!confirm('确定要清空对话历史吗？此操作不可撤销。')) return

    setIsClearing(true)
    try {
      await clearHistory(store.sessionId)
      store.clearMessages()
    } catch (err) {
      store.setError(err instanceof Error ? err.message : '清空历史失败')
    } finally {
      setIsClearing(false)
    }
  }

  return (
    <div className="w-80 flex-shrink-0 border-l border-[#e5e5e5] bg-white flex flex-col">
      {/* 文件状态头 */}
      <div className="h-10 border-b border-[#e5e5e5] px-4 flex items-center gap-2 flex-shrink-0">
        {sessionState?.filename ? (
          <>
            <span className="text-sm font-medium text-[#111] truncate flex-1">
              {sessionState.filename}
            </span>
            {sessionState.version > 0 && (
              <span className="text-xs text-[#999]">v{sessionState.version}</span>
            )}
            <button
              onClick={handleClearHistory}
              disabled={isClearing || store.messages.length === 0}
              className="text-xs text-[#666] hover:text-[#111] disabled:text-[#ccc] disabled:cursor-not-allowed"
              title="清空对话历史"
            >
              {isClearing ? '清空中...' : '清空'}
            </button>
          </>
        ) : (
          <span className="text-sm text-[#bbb]">未打开文件</span>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="px-4 py-2 text-xs text-[#cc0000] border-b border-[#e5e5e5] bg-[#fff5f5]">
          {error}
        </div>
      )}

      {/* 对话历史 */}
      <MessageList messages={store.messages} isStreaming={store.isStreaming} />

      {/* 输入区 */}
      <ChatInput store={store} onSend={sendMessage} />
    </div>
  )
}
