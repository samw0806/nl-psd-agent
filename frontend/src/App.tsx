import { useEffect } from 'react'
import { useSession } from './hooks/useSession'
import { PreviewCanvas } from './components/PreviewCanvas'
import { Toolbar } from './components/Toolbar'
import { ChatPanel } from './components/ChatPanel'
import { previewUrl } from './api/client'

function App() {
  const store = useSession()

  useEffect(() => {
    store.initSession()
  }, [])

  const resolvedPreviewUrl = store.sessionId && store.sessionState?.has_file
    ? (store.previewUrl ?? previewUrl(store.sessionId, store.previewVersion))
    : null

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-white">
      {/* 顶栏 */}
      <header className="h-10 border-b border-[#e5e5e5] flex items-center px-4 flex-shrink-0">
        <span className="text-sm font-semibold text-[#111] tracking-tight">
          ◆ NL-PSD Agent
        </span>
      </header>

      {/* 主体：左侧预览 + 右侧面板 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：预览区 + 工具栏 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <PreviewCanvas
            previewUrl={resolvedPreviewUrl}
            previewVersion={store.previewVersion}
          />
          <Toolbar store={store} />
        </div>

        {/* 右侧：Chat 面板 */}
        <ChatPanel store={store} />
      </div>
    </div>
  )
}

export default App
