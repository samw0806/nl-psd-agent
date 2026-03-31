// components/Toolbar.tsx — 撤销/重做/导出工具栏
import { SessionStore } from '../hooks/useSession'

interface Props {
  store: SessionStore
}

export function Toolbar({ store }: Props) {
  const { sessionState, undo, redo, exportAs, isStreaming } = store

  const canUndo = sessionState?.can_undo ?? false
  const canRedo = sessionState?.can_redo ?? false
  const hasFile = sessionState?.has_file ?? false

  return (
    <div className="h-10 border-t border-[#e5e5e5] bg-white flex items-center px-4 gap-2 text-sm flex-shrink-0">
      <button
        onClick={() => undo()}
        disabled={!canUndo || isStreaming}
        className="flex items-center gap-1 px-3 py-1 rounded border border-[#e5e5e5] text-[#111] disabled:text-[#ccc] disabled:cursor-not-allowed hover:bg-[#fafafa] transition-colors"
        title="撤销 (⌘Z)"
      >
        ← 撤销
      </button>
      <button
        onClick={() => redo()}
        disabled={!canRedo || isStreaming}
        className="flex items-center gap-1 px-3 py-1 rounded border border-[#e5e5e5] text-[#111] disabled:text-[#ccc] disabled:cursor-not-allowed hover:bg-[#fafafa] transition-colors"
        title="重做 (⌘⇧Z)"
      >
        重做 →
      </button>

      <div className="w-px h-5 bg-[#e5e5e5] mx-1" />

      <button
        onClick={() => exportAs('png')}
        disabled={!hasFile || isStreaming}
        className="flex items-center gap-1 px-3 py-1 rounded border border-[#e5e5e5] text-[#111] disabled:text-[#ccc] disabled:cursor-not-allowed hover:bg-[#fafafa] transition-colors"
      >
        导出 PNG ↓
      </button>
      <button
        onClick={() => exportAs('jpg')}
        disabled={!hasFile || isStreaming}
        className="flex items-center gap-1 px-3 py-1 rounded border border-[#e5e5e5] text-[#111] disabled:text-[#ccc] disabled:cursor-not-allowed hover:bg-[#fafafa] transition-colors"
      >
        导出 JPG ↓
      </button>

      <div className="ml-auto text-[#999] text-xs">
        {sessionState?.filename && (
          <span>{sessionState.filename}</span>
        )}
      </div>
    </div>
  )
}
