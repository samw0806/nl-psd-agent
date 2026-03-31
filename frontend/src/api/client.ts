// api/client.ts — API 调用封装

// 开发时由 vite proxy 转发 /api 到 localhost:8000；生产构建时可通过 VITE_API_BASE 指定
const BASE = import.meta.env.VITE_API_BASE ?? ''

export interface SessionState {
  session_id: string
  version: number
  filename: string | null
  can_undo: boolean
  can_redo: boolean
  has_file: boolean
}

export async function createSession(): Promise<SessionState> {
  const res = await fetch(`${BASE}/api/sessions`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export async function getSession(sid: string): Promise<SessionState> {
  const res = await fetch(`${BASE}/api/sessions/${sid}`)
  if (!res.ok) throw new Error('Session not found')
  return res.json()
}

export async function uploadPSD(sid: string, file: File): Promise<SessionState> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/sessions/${sid}/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}

export async function undoSession(sid: string): Promise<SessionState> {
  const res = await fetch(`${BASE}/api/sessions/${sid}/undo`, { method: 'POST' })
  if (!res.ok) throw new Error('Undo failed')
  return res.json()
}

export async function redoSession(sid: string): Promise<SessionState> {
  const res = await fetch(`${BASE}/api/sessions/${sid}/redo`, { method: 'POST' })
  if (!res.ok) throw new Error('Redo failed')
  return res.json()
}

export async function exportFile(sid: string, format: 'png' | 'jpg'): Promise<void> {
  const res = await fetch(`${BASE}/api/sessions/${sid}/export?format=${format}`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error('Export failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const cd = res.headers.get('content-disposition') ?? ''
  const match = cd.match(/filename="([^"]+)"/)
  a.download = match ? match[1] : `export.${format}`
  a.click()
  URL.revokeObjectURL(url)
}

export function previewUrl(sid: string, t: number): string {
  return `${BASE}/api/sessions/${sid}/preview?t=${t}`
}

export function chatUrl(sid: string, message: string): string {
  return `${BASE}/api/sessions/${sid}/chat?message=${encodeURIComponent(message)}`
}

export async function clearHistory(sid: string): Promise<void> {
  const res = await fetch(`${BASE}/api/sessions/${sid}/clear-history`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error('Clear history failed')
}

