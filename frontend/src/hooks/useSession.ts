// hooks/useSession.ts

import { useState, useCallback } from 'react'
import {
  createSession,
  uploadPSD,
  undoSession,
  redoSession,
  exportFile,
  SessionState,
} from '../api/client'

export interface ToolCallEvent {
  tool: string
  tool_use_id?: string
  status: 'running' | 'done'
  args?: Record<string, unknown>
  output?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolCalls?: ToolCallEvent[]
}

export interface SessionStore {
  sessionId: string | null
  sessionState: SessionState | null
  previewUrl: string | null
  previewVersion: number
  messages: Message[]
  isStreaming: boolean
  error: string | null
  initSession: () => Promise<void>
  uploadFile: (file: File) => Promise<void>
  undo: () => Promise<void>
  redo: () => Promise<void>
  exportAs: (format: 'png' | 'jpg') => Promise<void>
  appendMessage: (msg: Message) => void
  updateLastAssistantMessage: (updater: (msg: Message) => Message) => void
  clearMessages: () => void
  setPreview: (url: string) => void
  setStreaming: (v: boolean) => void
  setError: (e: string | null) => void
  refreshPreview: () => void
}

let msgCounter = 0
function nextId() {
  return String(++msgCounter)
}

export function useSession(): SessionStore {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionState, setSessionState] = useState<SessionState | null>(null)
  const [previewUrl, setPreviewUrlState] = useState<string | null>(null)
  const [previewVersion, setPreviewVersion] = useState(0)
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const initSession = useCallback(async () => {
    const s = await createSession()
    setSessionId(s.session_id)
    setSessionState(s)
    setMessages([])
  }, [])

  const uploadFile = useCallback(
    async (file: File) => {
      if (!sessionId) return
      const s = await uploadPSD(sessionId, file)
      setSessionState(s)
      setPreviewVersion((v) => v + 1)
    },
    [sessionId]
  )

  const undo = useCallback(async () => {
    if (!sessionId) return
    const s = await undoSession(sessionId)
    setSessionState(s)
    setPreviewVersion((v) => v + 1)
  }, [sessionId])

  const redo = useCallback(async () => {
    if (!sessionId) return
    const s = await redoSession(sessionId)
    setSessionState(s)
    setPreviewVersion((v) => v + 1)
  }, [sessionId])

  const exportAs = useCallback(
    async (format: 'png' | 'jpg') => {
      if (!sessionId) return
      await exportFile(sessionId, format)
    },
    [sessionId]
  )

  const appendMessage = useCallback((msg: Message) => {
    setMessages((prev) => [...prev, { ...msg, id: msg.id || nextId() }])
  }, [])

  const updateLastAssistantMessage = useCallback(
    (updater: (msg: Message) => Message) => {
      setMessages((prev) => {
        const idx = [...prev].reverse().findIndex((m) => m.role === 'assistant')
        if (idx === -1) return prev
        const realIdx = prev.length - 1 - idx
        const updated = [...prev]
        updated[realIdx] = updater(updated[realIdx])
        return updated
      })
    },
    []
  )

  const setPreview = useCallback((url: string) => {
    setPreviewUrlState(url)
    setPreviewVersion((v) => v + 1)
  }, [])

  const refreshPreview = useCallback(() => {
    setPreviewVersion((v) => v + 1)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    sessionId,
    sessionState,
    previewUrl,
    previewVersion,
    messages,
    isStreaming,
    error,
    initSession,
    uploadFile,
    undo,
    redo,
    exportAs,
    appendMessage,
    updateLastAssistantMessage,
    clearMessages,
    setPreview,
    setStreaming,
    setError,
    refreshPreview,
  }
}
