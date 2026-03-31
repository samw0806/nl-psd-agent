// components/ChatInput.tsx — 输入框 + 文件上传
import { useState, useRef, KeyboardEvent } from 'react'
import { SessionStore } from '../hooks/useSession'

interface Props {
  store: SessionStore
  onSend: (text: string) => void
}

export function ChatInput({ store, onSend }: Props) {
  const [text, setText] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const { isStreaming, sessionState, uploadFile } = store

  const hasFile = sessionState?.has_file ?? false
  const hasSession = !!store.sessionId

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || isStreaming || !hasFile) return
    onSend(trimmed)
    setText('')
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await uploadFile(file)
    e.target.value = ''
  }

  return (
    <div className="border-t border-[#e5e5e5] bg-white p-3 flex-shrink-0">
      <div className="flex items-end gap-2 border border-[#e5e5e5] rounded-lg px-3 py-2 bg-[#fafafa]">
        <button
          onClick={() => fileRef.current?.click()}
          disabled={!hasSession}
          className="text-[#666] hover:text-[#111] disabled:text-[#ccc] transition-colors flex-shrink-0 mb-1"
          title="上传 PSD 文件"
        >
          📎
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".psd,.psb"
          onChange={handleFile}
          className="hidden"
        />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder={hasFile ? '输入指令… (Enter 发送，Shift+Enter 换行)' : '请先上传 PSD 文件'}
          disabled={!hasFile || isStreaming}
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-sm text-[#111] placeholder:text-[#bbb] disabled:cursor-not-allowed min-h-[24px] max-h-32"
          style={{ lineHeight: '1.5' }}
          onInput={(e) => {
            const el = e.currentTarget
            el.style.height = 'auto'
            el.style.height = `${Math.min(el.scrollHeight, 128)}px`
          }}
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || !hasFile || isStreaming}
          className="text-[#111] hover:text-[#333] disabled:text-[#ccc] disabled:cursor-not-allowed transition-colors flex-shrink-0 mb-1 font-medium"
          title="发送"
        >
          {isStreaming ? '…' : '↑'}
        </button>
      </div>
    </div>
  )
}
