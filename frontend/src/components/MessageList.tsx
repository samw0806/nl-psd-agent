// components/MessageList.tsx — 对话历史渲染
import { useEffect, useRef } from 'react'
import { Message } from '../hooks/useSession'
import { ToolCallStatus } from './ToolCallStatus'

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#bbb] text-sm select-none">
        上传 PSD 文件后开始对话
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-4">
      {messages.map((msg) => (
        <div key={msg.id} className={msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
          {msg.role === 'user' ? (
            <div className="max-w-[85%] bg-[#111] text-white text-sm rounded-lg px-3 py-2">
              {msg.content}
            </div>
          ) : (
            <div className="max-w-[95%] text-sm text-[#111]">
              {msg.content && (
                <div className="message-content leading-relaxed">{msg.content}</div>
              )}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <ToolCallStatus toolCalls={msg.toolCalls} />
              )}
              {isStreaming && msg === messages[messages.length - 1] && !msg.content && (
                <span className="text-[#999] text-xs">思考中…</span>
              )}
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
