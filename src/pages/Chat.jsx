import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Send, CheckCircle, Bot, BarChart3, Download, AlertTriangle, FileText,
  MessageSquarePlus, Trash2, Clock3, PanelLeftOpen, PanelLeftClose,
} from 'lucide-react'
import clsx from 'clsx'
import { MiniJobCard } from '../components/JobCard'
import { AIBadge, TypingIndicator, Button } from '../components/ui'
import { INITIAL_MESSAGES, QUICK_ACTIONS, SKILL_DATA } from '../data/mockData'
import {
  createChatSessionId,
  resetChatSession,
  sendChatMessage,
  setChatSessionId,
} from '../services/chatService'
import { useAuth } from '../context/AuthContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ─── Inline skill bar chart for chat ─────────────────────────────────────────
function InlineSkillChart({ data, title = 'Top Skills Demand 2025', unit = '%' }) {
  const chartData = data.slice(0, 8)
  return (
    <div className="mt-3 bg-gray-50 rounded-lg p-3 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-text-primary">📊 {title}</p>
        <button className="text-2xs text-text-muted hover:text-violet flex items-center gap-1">
          <Download size={10} /> Export
        </button>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(130, chartData.length * 28)}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid horizontal={false} stroke="#E5E7EB" />
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="skill" tick={{ fontSize: 10, fill: '#6B7280' }} tickLine={false} axisLine={false} width={70} />
          <Tooltip
            content={({ active, payload }) => active && payload?.[0] ? (
              <div className="bg-white shadow-card rounded px-2 py-1 text-xs border border-gray-100">
                <b>{payload[0].payload.skill}</b>: {payload[0].value} {unit}
              </div>
            ) : null}
          />
          <Bar dataKey="pct" radius={[0, 3, 3, 0]} maxBarSize={12}>
            {chartData.map((_, i) => (
              <Cell
                key={i}
                fill={['#4338CA','#7C3AED','#10B981','#6366F1','#A78BFA','#0EA5E9','#F59E0B','#EF4444'][i]}
              />
            ))}
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
function isCoverLetterIntent(text) {
  const normalized = text.toLowerCase()
  return (
    normalized.includes('cover letter') ||
    normalized.includes('thư xin việc') ||
    normalized.includes('thư ứng tuyển') ||
    normalized.includes('cv')
  )
}

function attachCoverLetterCta(response) {
  return {
    ...response,
    action: {
      label: 'Mở trang Upload CV',
      to: '/cover-letter',
      icon: 'file',
      variant: 'mint',
      hint: 'Upload CV ở trang Write Cover Letter, chọn job đang apply, rồi bấm “Tạo lại với AI”.',
    },
  }
}

const MAX_STORED_CONVERSATIONS = 20

function chatStorageKey(userId) {
  return `techjob_chat_conversations_${userId || 'guest'}`
}

function cloneInitialMessages() {
  return INITIAL_MESSAGES.map(message => ({
    ...message,
    timestamp: new Date(message.timestamp).toISOString(),
  }))
}

function normalizeMessage(message) {
  return {
    ...message,
    timestamp: message.timestamp
      ? new Date(message.timestamp).toISOString()
      : new Date().toISOString(),
  }
}

function createConversation() {
  const now = new Date().toISOString()
  return {
    id: globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}`,
    sessionId: createChatSessionId(),
    title: 'Cuộc trò chuyện mới',
    createdAt: now,
    updatedAt: now,
    messages: cloneInitialMessages(),
  }
}

function loadConversations(userId) {
  try {
    const raw = localStorage.getItem(chatStorageKey(userId))
    const parsed = raw ? JSON.parse(raw) : null
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map(conversation => ({
        ...conversation,
        sessionId: conversation.sessionId || createChatSessionId(),
        messages: (conversation.messages || cloneInitialMessages()).map(normalizeMessage),
      }))
    }
  } catch {
    // Ignore malformed localStorage and start fresh.
  }
  return [createConversation()]
}

function saveConversations(userId, conversations) {
  const trimmed = conversations
    .slice()
    .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    .slice(0, MAX_STORED_CONVERSATIONS)
  localStorage.setItem(chatStorageKey(userId), JSON.stringify(trimmed))
  return trimmed
}

function buildConversationTitle(text) {
  const clean = text.replace(/\s+/g, ' ').trim()
  if (!clean) return 'Cuộc trò chuyện mới'
  return clean.length > 42 ? `${clean.slice(0, 42)}...` : clean
}

function formatConversationTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }) +
    ' ' +
    date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

function ChatHistoryPanel({
  conversations,
  activeConversationId,
  onSelect,
  onNew,
  onDelete,
  collapsed,
  onToggle,
}) {
  return (
    <aside className={clsx(
      'hidden md:flex flex-col border-r border-gray-100 bg-white transition-all shrink-0',
      collapsed ? 'w-14' : 'w-72'
    )}>
      <div className="h-16 px-3 border-b border-gray-100 flex items-center gap-2">
        <button
          type="button"
          onClick={onToggle}
          title={collapsed ? 'Mở lịch sử chat' : 'Thu gọn lịch sử chat'}
          className="p-2 rounded-lg text-text-muted hover:bg-gray-100 hover:text-text-primary transition-colors"
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
        {!collapsed && (
          <>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-text-primary">Lịch sử chat</p>
              <p className="text-2xs text-text-muted">{conversations.length} cuộc trò chuyện</p>
            </div>
            <button
              type="button"
              onClick={onNew}
              title="Tạo cuộc trò chuyện mới"
              className="p-2 rounded-lg text-violet hover:bg-violet-bg transition-colors"
            >
              <MessageSquarePlus size={16} />
            </button>
          </>
        )}
      </div>

      {!collapsed && (
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {conversations.map(conversation => (
            <button
              key={conversation.id}
              type="button"
              onClick={() => onSelect(conversation.id)}
              className={clsx(
                'group w-full text-left rounded-lg border px-3 py-2.5 transition-all',
                activeConversationId === conversation.id
                  ? 'border-violet/30 bg-violet-bg'
                  : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50'
              )}
            >
              <div className="flex items-start gap-2">
                <div className={clsx(
                  'w-7 h-7 rounded-lg flex items-center justify-center shrink-0',
                  activeConversationId === conversation.id ? 'bg-violet text-white' : 'bg-gray-100 text-text-muted'
                )}>
                  <Bot size={13} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-text-primary truncate">{conversation.title}</p>
                  <p className="text-2xs text-text-muted mt-0.5 flex items-center gap-1">
                    <Clock3 size={10} /> {formatConversationTime(conversation.updatedAt)}
                  </p>
                </div>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={event => {
                    event.stopPropagation()
                    onDelete(conversation.id)
                  }}
                  onKeyDown={event => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      event.stopPropagation()
                      onDelete(conversation.id)
                    }
                  }}
                  title="Xoá cuộc trò chuyện"
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded text-text-muted hover:text-red-500 hover:bg-red-50 transition-all"
                >
                  <Trash2 size={12} />
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {collapsed && (
        <div className="p-2">
          <button
            type="button"
            onClick={onNew}
            title="Tạo cuộc trò chuyện mới"
            className="w-10 h-10 rounded-lg text-violet hover:bg-violet-bg flex items-center justify-center transition-colors"
          >
            <MessageSquarePlus size={16} />
          </button>
        </div>
      )}
    </aside>
  )
}

function MobileHistoryBar({ conversations, activeConversationId, onSelect, onNew, disabled }) {
  return (
    <div className="md:hidden px-4 py-2 bg-white border-b border-gray-100 flex items-center gap-2 shrink-0">
      <select
        value={activeConversationId || ''}
        onChange={event => onSelect(event.target.value)}
        disabled={disabled}
        aria-label="Chọn lịch sử trò chuyện"
        className="min-w-0 flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-violet"
      >
        {conversations.map(conversation => (
          <option key={conversation.id} value={conversation.id}>
            {conversation.title} - {formatConversationTime(conversation.updatedAt)}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={onNew}
        disabled={disabled}
        title="Tạo cuộc trò chuyện mới"
        className="p-2 rounded-lg text-violet hover:bg-violet-bg disabled:opacity-50 transition-colors"
      >
        <MessageSquarePlus size={16} />
      </button>
    </div>
  )
}

function MessageBubble({ msg, onAction }) {
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
          {/* Full Markdown/GFM: headings, lists, tables, emphasis and links */}
          {msg.content && (
            <div className="text-text-primary leading-relaxed overflow-x-auto">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h3: props => <h3 className="text-base font-bold mt-3 mb-2" {...props} />,
                  h4: props => <h4 className="text-sm font-semibold mt-3 mb-1.5" {...props} />,
                  p: props => <p className="my-1.5" {...props} />,
                  ul: props => <ul className="list-disc pl-5 my-2 space-y-1" {...props} />,
                  ol: props => <ol className="list-decimal pl-5 my-2 space-y-1" {...props} />,
                  table: props => (
                    <table className="w-full min-w-[420px] border-collapse my-3 text-xs" {...props} />
                  ),
                  th: props => (
                    <th className="border border-gray-200 bg-gray-50 px-3 py-2 text-left font-semibold" {...props} />
                  ),
                  td: props => (
                    <td className="border border-gray-200 px-3 py-2 align-top" {...props} />
                  ),
                  a: props => (
                    <a className="text-violet underline" target="_blank" rel="noreferrer" {...props} />
                  ),
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Inline chart */}
          {msg.showChart && (
            msg.charts?.length > 0
              ? msg.charts.map((chart, index) => (
                  <InlineSkillChart
                    key={`${chart.title}-${index}`}
                    data={(chart.labels || []).map((skill, itemIndex) => ({
                      skill,
                      pct: chart.values?.[itemIndex] ?? 0,
                    }))}
                    title={chart.title}
                    unit={chart.ylabel || ''}
                  />
                ))
              : <InlineSkillChart data={SKILL_DATA} />
          )}

          {/* Job cards */}
          {msg.jobCards?.length > 0 && (
            <div className="mt-3 space-y-2">
              {msg.jobCards.map(job => <MiniJobCard key={job.id} job={job} />)}
            </div>
          )}

          {/* Tools used */}
          {msg.toolsUsed?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {msg.toolsUsed.map(tool => (
                <AIBadge key={tool} variant="gray">Tool: {tool}</AIBadge>
              ))}
            </div>
          )}

          {/* Follow-up */}
          {msg.followUp && (
            <p className="mt-3 text-sm text-text-secondary">{msg.followUp}</p>
          )}

          {/* Action CTA */}
          {msg.action && (
            <div className="mt-3">
              <Button
                variant={msg.action.variant || 'primary'}
                size="sm"
                onClick={() => onAction?.(msg.action)}
              >
                {msg.action.icon === 'file' && <FileText size={13} />}
                {msg.action.label}
              </Button>
              {msg.action.hint && (
                <p className="text-xs text-text-muted mt-2">{msg.action.hint}</p>
              )}
            </div>
          )}
        </div>

        {/* Source label */}
        {msg.type === 'vector' && (
          <div className="mt-1 ml-1">
            <AIBadge variant="gray">🔍 Nguồn: Vector DB</AIBadge>
          </div>
        )}
        {msg.type === 'data' && msg.toolsUsed?.length > 0 && (
          <div className="mt-1 ml-1">
            <AIBadge variant="gray">🗄️ Nguồn: Data Warehouse</AIBadge>
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
  const { user } = useAuth()
  const userId = user?.id || 'guest'
  const [conversations, setConversations] = useState(() => loadConversations(userId))
  const [activeConversationId, setActiveConversationId] = useState(() => conversations[0]?.id)
  const activeConversation = conversations.find(item => item.id === activeConversationId) || conversations[0]
  const messages = activeConversation?.messages || cloneInitialMessages()
  const [input, setInput]       = useState('')
  const [typing, setTyping]     = useState(false)
  const [streamText, setStreamText] = useState('')
  const [fallback, setFallback] = useState(false)
  const [historyCollapsed, setHistoryCollapsed] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    const loaded = loadConversations(userId)
    setConversations(loaded)
    setActiveConversationId(loaded[0]?.id)
    setInput('')
    setTyping(false)
    setStreamText('')
    setFallback(false)
  }, [userId])

  useEffect(() => {
    if (activeConversation?.sessionId) {
      setChatSessionId(activeConversation.sessionId)
    }
  }, [activeConversation?.sessionId])

  const persistConversations = useCallback((updater) => {
    setConversations(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      return saveConversations(userId, next)
    })
  }, [userId])

  const updateActiveConversation = useCallback((patcher) => {
    const now = new Date().toISOString()
    persistConversations(prev => prev.map(conversation => {
      if (conversation.id !== activeConversationId) return conversation
      const patch = typeof patcher === 'function' ? patcher(conversation) : patcher
      return {
        ...conversation,
        ...patch,
        updatedAt: patch.updatedAt || now,
      }
    }))
  }, [activeConversationId, persistConversations])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing, streamText])

  const sendMessage = useCallback(async (text) => {
    const content = text || input.trim()
    if (!content || typing || !activeConversation) return

    setInput('')
    const userMsg = {
      id: Date.now(),
      role: 'user',
      type: 'text',
      content,
      timestamp: new Date().toISOString(),
    }
    const nextMessages = [...messages, userMsg]
    updateActiveConversation(conversation => ({
      title: conversation.title === 'Cuộc trò chuyện mới'
        ? buildConversationTitle(content)
        : conversation.title,
      messages: nextMessages,
    }))
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
      aiResp = await sendChatMessage(content, nextMessages)
      if (aiResp?.error) {
        throw new Error('AI backend returned an error response')
      }
      if (isCoverLetterIntent(content)) {
        aiResp = attachCoverLetterCta(aiResp)
      }
    } catch (err) {
      // FR-9 / NFR-3 — Tầng 3 & 4 lỗi → vẫn gợi ý dùng Tầng 1 (bộ lọc thủ công)
      setTyping(false)
      setFallback(true)
      return
    }

    // Keep long analytical answers responsive. Streaming every word made a
    // complete backend response look truncated for 10-20 seconds.
    setTyping(false)
    const words = aiResp.content.split(' ')
    let streamed = ''
    const wordDelay = words.length > 180 ? 2 : 12
    for (let i = 0; i < words.length; i++) {
      await new Promise(r => setTimeout(r, wordDelay))
      streamed += (i === 0 ? '' : ' ') + words[i]
      setStreamText(streamed)
    }
    setStreamText('')

    const assistantMsg = {
      id: Date.now(),
      role: 'assistant',
      ...aiResp,
      timestamp: new Date().toISOString(),
    }
    updateActiveConversation({ messages: [...nextMessages, assistantMsg] })
    inputRef.current?.focus()
  }, [activeConversation, input, messages, typing, updateActiveConversation])

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const handleMessageAction = action => {
    if (action?.to) navigate(action.to)
  }

  const handleNewConversation = () => {
    const sessionId = resetChatSession()
    const conversation = {
      ...createConversation(),
      sessionId,
    }
    persistConversations(prev => [conversation, ...prev])
    setActiveConversationId(conversation.id)
    setInput('')
    setTyping(false)
    setStreamText('')
    setFallback(false)
    inputRef.current?.focus()
  }

  const handleSelectConversation = id => {
    if (typing) return
    const conversation = conversations.find(item => item.id === id)
    if (!conversation) return
    setActiveConversationId(id)
    setChatSessionId(conversation.sessionId)
    setInput('')
    setStreamText('')
    setFallback(false)
    inputRef.current?.focus()
  }

  const handleDeleteConversation = id => {
    if (typing) return
    const remaining = conversations.filter(item => item.id !== id)
    const fallbackConversation = remaining.length > 0 ? null : createConversation()
    const nextConversations = remaining.length > 0 ? remaining : [fallbackConversation]
    persistConversations(nextConversations)
    if (id === activeConversationId) {
      const nextConversation = remaining[0] || fallbackConversation
      setActiveConversationId(nextConversation.id)
      setChatSessionId(nextConversation.sessionId)
    }
  }

  return (
    <div className="flex h-[calc(100vh-64px)] animate-fade-in -m-6 bg-bg">
      <ChatHistoryPanel
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
        collapsed={historyCollapsed}
        onToggle={() => setHistoryCollapsed(prev => !prev)}
      />

      <div className="flex flex-col min-w-0 flex-1">
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
            <p className="text-2xs text-text-secondary">Powered by AI &amp; Live Market Data</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleNewConversation}
          title="Bắt đầu cuộc trò chuyện mới"
          aria-label="Bắt đầu cuộc trò chuyện mới"
          className="p-2 rounded-lg text-text-muted hover:bg-gray-100 transition-colors"
        >
          <MessageSquarePlus size={16} />
        </button>
      </div>

      <MobileHistoryBar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        disabled={typing}
      />

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
        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} onAction={handleMessageAction} />
        ))}

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
    </div>
  )
}
