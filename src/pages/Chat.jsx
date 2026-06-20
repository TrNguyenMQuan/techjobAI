import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, MoreVertical, CheckCircle, Bot, BarChart3, Download, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import { MiniJobCard } from '../components/JobCard'
import { AIBadge, TypingIndicator, Button } from '../components/ui'
import { INITIAL_MESSAGES, QUICK_ACTIONS, SKILL_DATA } from '../data/mockData'
import { sendChatMessage } from '../services/chatService'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'

// ─── Inline skill bar chart for chat ─────────────────────────────────────────
function InlineSkillChart({ data }) {
  const top5 = data.slice(0, 5)
  return (
    <div className="mt-3 bg-gray-50 rounded-lg p-3 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-text-primary">📊 Top Skills Demand 2025</p>
        <button className="text-2xs text-text-muted hover:text-violet flex items-center gap-1">
          <Download size={10} /> Export
        </button>
      </div>
      <ResponsiveContainer width="100%" height={130}>
        <BarChart data={top5} layout="vertical" margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid horizontal={false} stroke="#E5E7EB" />
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="skill" tick={{ fontSize: 10, fill: '#6B7280' }} tickLine={false} axisLine={false} width={70} />
          <Tooltip
            content={({ active, payload }) => active && payload?.[0] ? (
              <div className="bg-white shadow-card rounded px-2 py-1 text-xs border border-gray-100">
                <b>{payload[0].payload.skill}</b>: {payload[0].value}%
              </div>
            ) : null}
          />
          <Bar dataKey="pct" radius={[0, 3, 3, 0]} maxBarSize={12}>
            {top5.map((_, i) => <Cell key={i} fill={['#4338CA','#7C3AED','#10B981','#6366F1','#A78BFA'][i]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-1 mt-1">
        <AIBadge variant="mint"><BarChart3 size={9} /> Generated from live data</AIBadge>
      </div>
    </div>
  )
}

// ─── End of inline chart component ───────────────────────────────────────────

// ─── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="bubble-user text-sm whitespace-pre-line">{msg.content}</div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 animate-float-up">
      <div className="w-8 h-8 rounded-full bg-indigo flex items-center justify-center shrink-0 mt-0.5">
        <Bot size={14} className="text-white" />
      </div>
      <div className="max-w-xl flex-1">
        <div className="bubble-ai text-sm">
          {/* Text content — handle simple markdown */}
          {msg.content && (
            <div className="whitespace-pre-line text-text-primary leading-relaxed">
              {msg.content.split('\n').map((line, i) => {
                // Bold **text**
                const parts = line.split(/(\*\*[^*]+\*\*)/g)
                return (
                  <p key={i} className={line === '' ? 'my-1' : ''}>
                    {parts.map((part, j) =>
                      part.startsWith('**') && part.endsWith('**')
                        ? <strong key={j}>{part.slice(2, -2)}</strong>
                        : part
                    )}
                  </p>
                )
              })}
            </div>
          )}

          {/* Inline chart */}
          {msg.showChart && <InlineSkillChart data={SKILL_DATA} />}

          {/* Job cards */}
          {msg.jobCards?.length > 0 && (
            <div className="mt-3 space-y-2">
              {msg.jobCards.map(job => <MiniJobCard key={job.id} job={job} />)}
            </div>
          )}

          {/* Follow-up */}
          {msg.followUp && (
            <p className="mt-3 text-sm text-text-secondary">{msg.followUp}</p>
          )}
        </div>

        {/* Source label */}
        {msg.type === 'mixed' && (
          <div className="mt-1 ml-1">
            <AIBadge variant="gray">🔍 Nguồn: Vector DB</AIBadge>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-2xs text-text-muted mt-1 ml-1">
          {new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}

// ─── Main Chat page ───────────────────────────────────────────────────────────
export default function Chat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState(INITIAL_MESSAGES)
  const [input, setInput]       = useState('')
  const [typing, setTyping]     = useState(false)
  const [streamText, setStreamText] = useState('')
  const [fallback, setFallback] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing, streamText])

  const sendMessage = useCallback(async (text) => {
    const content = text || input.trim()
    if (!content || typing) return

    setInput('')
    const userMsg = {
      id: Date.now(),
      role: 'user',
      type: 'text',
      content,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setTyping(true)
    setStreamText('')
    setFallback(false)

    let aiResp
    try {
      // Simulate network + "thinking" delay before the response is ready
      await new Promise(r => setTimeout(r, 600 + Math.random() * 500))
      // Special debug trigger to demo the Graceful Degradation state (NFR-3)
      if (content.trim().toLowerCase() === '/simulate-error') {
        throw new Error('AI backend unreachable (simulated)')
      }
      aiResp = await sendChatMessage(content, messages)
    } catch (err) {
      // FR-9 / NFR-3 — Tầng 3 & 4 lỗi → vẫn gợi ý dùng Tầng 1 (bộ lọc thủ công)
      setTyping(false)
      setFallback(true)
      return
    }

    // Simulate token-by-token streaming
    setTyping(false)
    const words = aiResp.content.split(' ')
    let streamed = ''
    for (let i = 0; i < words.length; i++) {
      await new Promise(r => setTimeout(r, 18 + Math.random() * 20))
      streamed += (i === 0 ? '' : ' ') + words[i]
      setStreamText(streamed)
    }
    setStreamText('')

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'assistant',
      ...aiResp,
      timestamp: new Date(),
    }])
    inputRef.current?.focus()
  }, [input, typing, messages])

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] animate-fade-in -m-6">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-100 bg-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-indigo flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-text-primary">TechJob AI Assistant</p>
              <CheckCircle size={13} className="text-mint" />
            </div>
            <p className="text-2xs text-text-secondary">Powered by GPT-4 &amp; Live Market Data</p>
          </div>
        </div>
        <button className="p-2 rounded-lg text-text-muted hover:bg-gray-100 transition-colors">
          <MoreVertical size={16} />
        </button>
      </div>

      {/* AI Fallback banner — NFR-3 Graceful Degradation: Tầng 3/4 lỗi, Tầng 1/2 vẫn hoạt động */}
      {fallback && (
        <div className="px-6 py-3 bg-yellow-50 border-b border-yellow-200 flex items-center gap-3 shrink-0 animate-fade-in">
          <AlertTriangle size={16} className="text-yellow-600 shrink-0" />
          <p className="text-sm text-yellow-800 flex-1">
            AI tạm thời không khả dụng. Bạn có thể dùng bộ lọc thủ công để tìm việc.
          </p>
          <Button variant="secondary" size="sm" onClick={() => navigate('/jobs')}>
            Dùng bộ lọc
          </Button>
          <button onClick={() => setFallback(false)} className="text-yellow-600 hover:text-yellow-800 text-xs">✕</button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 bg-bg">
        {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}

        {/* Streaming bubble */}
        {streamText && (
          <div className="flex items-start gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-indigo flex items-center justify-center shrink-0">
              <Bot size={14} className="text-white" />
            </div>
            <div className="bubble-ai text-sm text-text-primary whitespace-pre-line">
              {streamText}<span className="inline-block w-0.5 h-3.5 bg-indigo ml-0.5 animate-pulse" />
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {typing && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo flex items-center justify-center shrink-0">
              <Bot size={14} className="text-white" />
            </div>
            <div className="bubble-ai">
              <TypingIndicator />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Quick actions */}
      <div className="px-6 py-2.5 bg-white border-t border-gray-100 flex gap-2 overflow-x-auto shrink-0">
        {QUICK_ACTIONS.map(qa => (
          <button
            key={qa.id}
            onClick={() => sendMessage(qa.prompt)}
            disabled={typing}
            className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 text-xs text-text-secondary
                       hover:border-violet hover:text-violet hover:bg-violet-bg transition-all disabled:opacity-50"
          >
            {qa.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="px-6 py-3 bg-white border-t border-gray-100 shrink-0">
        <div className="flex items-end gap-2 bg-gray-50 rounded-xl border border-gray-200 px-4 py-2
                        focus-within:border-violet focus-within:ring-2 focus-within:ring-violet/20 transition-all">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Nhập yêu cầu của bạn..."
            rows={1}
            disabled={typing}
            className="flex-1 resize-none bg-transparent text-sm text-text-primary placeholder:text-text-muted
                       focus:outline-none max-h-32 overflow-y-auto"
            style={{ height: '24px' }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || typing}
            className={clsx(
              'p-2 rounded-lg transition-all mb-0.5 shrink-0',
              input.trim() && !typing
                ? 'bg-indigo text-white hover:bg-indigo-dark active:scale-95'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-center text-2xs text-text-muted mt-2">
          TechJob AI có thể mắc sai sót. Hãy kiểm tra thông tin quan trọng.
        </p>
      </div>
    </div>
  )
}
