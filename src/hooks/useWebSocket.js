import { useRef, useCallback, useState } from 'react'
import { CHAT_WS_URL } from '../services/chatService'

/**
 * Thin wrapper around the native WebSocket API for the AI Assistant chat
 * (FR-7/FR-9). When no real backend is reachable it reports `fallback: true`
 * so the UI can show the "AI tạm thời không khả dụng" banner from the design
 * spec's Graceful Degradation principle (NFR-3) instead of crashing.
 *
 * Usage:
 *   const { status, send, fallback } = useWebSocket({ onMessage })
 */
export function useWebSocket({ onMessage, onError } = {}) {
  const wsRef = useRef(null)
  const [status, setStatus] = useState('idle') // idle | connecting | open | closed | error
  const [fallback, setFallback] = useState(false)

  const connect = useCallback((url = CHAT_WS_URL) => {
    try {
      setStatus('connecting')
      const ws = new WebSocket(url)

      ws.onopen = () => { setStatus('open'); setFallback(false) }
      ws.onmessage = (evt) => {
        try { onMessage?.(JSON.parse(evt.data)) } catch { onMessage?.(evt.data) }
      }
      ws.onerror = (err) => { setStatus('error'); setFallback(true); onError?.(err) }
      ws.onclose = () => setStatus('closed')

      wsRef.current = ws
    } catch (err) {
      // No backend available in this environment — fall back gracefully.
      setStatus('error')
      setFallback(true)
      onError?.(err)
    }
  }, [onMessage, onError])

  const send = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof payload === 'string' ? payload : JSON.stringify(payload))
      return true
    }
    return false // caller should fall back to chatService mock
  }, [])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  return { status, fallback, connect, disconnect, send }
}
