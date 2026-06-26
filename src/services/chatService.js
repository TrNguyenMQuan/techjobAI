import { api, mockDelay } from './api'
import { MOCK_JOBS, SKILL_DATA } from '../data/mockData'

// In production this connects to a real backend WebSocket / SSE endpoint that
// fronts the ReAct Agent (FR-7), Text-to-SQL (FR-10) and RAG (FR-11) pipeline.
// See hooks/useWebSocket.js for the connection + fallback logic. The mock
// implementation below returns a realistic canned response so the full chat
// UI (streaming, mini job cards, inline charts, RAG badges) can be demoed
// without a backend.
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'
const CHAT_TIMEOUT_MS = Number(import.meta.env.VITE_CHAT_TIMEOUT_MS || 90000)
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat'
const CHAT_SESSION_KEY = 'techjob_chat_session_id'

export function createChatSessionId() {
  const id = globalThis.crypto?.randomUUID?.()
    || `${Date.now()}-${Math.random().toString(36).slice(2)}`
  return `web-${id}`.slice(0, 100)
}

export function getChatSessionId() {
  let sessionId = sessionStorage.getItem(CHAT_SESSION_KEY)
  if (!sessionId) {
    sessionId = createChatSessionId()
    sessionStorage.setItem(CHAT_SESSION_KEY, sessionId)
  }
  return sessionId
}

export function setChatSessionId(sessionId) {
  if (!sessionId) return getChatSessionId()
  sessionStorage.setItem(CHAT_SESSION_KEY, sessionId)
  return sessionId
}

export function resetChatSession() {
  const sessionId = createChatSessionId()
  sessionStorage.setItem(CHAT_SESSION_KEY, sessionId)
  return sessionId
}

/**
 * Builds an AI response for a user prompt.
 * Swap the body of this function for a real backend call once it's
 * available — the shape `{ type, content, jobCards, showChart, followUp }`
 * is what <Chat /> expects.
 */
export async function sendChatMessage(text, _history = []) {
  if (!USE_MOCK) {
    try {
      const { data } = await api.post('/chat', null, {
        // Never share the backend's in-memory conversation history through the
        // global "default" session. Each browser tab owns an isolated session.
        params: { message: text, session_id: getChatSessionId() },
        // The first semantic-search request may need to warm the embedding
        // model. Do not inherit the short 15-second timeout used by normal APIs.
        timeout: CHAT_TIMEOUT_MS,
      })
      return {
        type: data.tools_used?.includes('semantic_search_tool') ? 'vector' : 'data',
        content: data.response,
        jobCards: [],
        showChart: (data.charts?.length || 0) > 0,
        toolsUsed: data.tools_used || [],
        charts: data.charts || [],
      }
    } catch (err) {
      console.error('Chat backend error:', err)
      return {
        type: 'text',
        content: 'Xin lỗi, tôi đang gặp sự cố khi kết nối tới hệ thống AI.',
        jobCards: [],
        showChart: false,
        error: true
      }
    }
  }

  // fallback to mock delay if USE_MOCK=true
  await mockDelay(300)
  const t = text.toLowerCase()

  if (t.includes('cover letter') || t.includes('thư ứng tuyển')) {
    return {
      type: 'text',
      content: `Tất nhiên! Để viết cover letter hiệu quả cho bạn, tôi cần thêm một vài thông tin:\n\n` +
        `• **Vị trí bạn đang apply**: Senior ReactJS Developer tại TechCorp Vietnam?\n` +
        `• **Số năm kinh nghiệm React**: ~3-5 năm?\n` +
        `• **Điểm mạnh nổi bật**: TypeScript, performance optimization?\n\n` +
        `Hoặc bạn có thể đến trang **Cover Letter** để tôi tự động lấy thông tin từ CV và job đã lưu của bạn! 🚀`,
      jobCards: [],
      showChart: false,
    }
  }

  if (t.includes('lương') || t.includes('salary') || t.includes('so sánh')) {
    return {
      type: 'text',
      content: `Dưới đây là mức lương trung bình (USD/tháng) trên thị trường IT Việt Nam theo kỹ năng:\n\n` +
        `**ReactJS** — Junior $500-800 · Mid $1,200-1,800 · Senior $2,000-3,000\n` +
        `**Python/AI** — Junior $600-900 · Mid $1,400-2,200 · Senior $2,500-4,000\n` +
        `**Go** — Junior $700-1,000 · Mid $1,600-2,500 · Senior $3,000-4,500\n\n` +
        `📈 **Go** và **Python/AI** đang có mức lương cao nhất và tăng trưởng nhanh nhất (+28% và +45% YoY).\n\n` +
        `Bạn muốn xem chi tiết cho kỹ năng nào không?`,
      jobCards: [],
      showChart: true,
    }
  }

  if (t.includes('kỹ năng') || t.includes('skill') || t.includes('hot') || t.includes('trending') || t.includes('phân tích')) {
    return {
      type: 'mixed',
      content: `Tôi đã phân tích xu hướng kỹ năng tháng 6/2025 từ dữ liệu thực tế của VietnamWorks và ITviec:\n\n` +
        `🔥 **Top emerging skills:**\n` +
        `• **Generative AI / LLMs**: tăng **+312%** YoY — nhu cầu bùng nổ do ChatGPT tích hợp vào sản phẩm\n` +
        `• **Go**: +45% — microservices demand tăng mạnh\n` +
        `• **DevSecOps**: +28% — cloud security focus\n\n` +
        `Dưới đây là biểu đồ top skills theo số lượng tin tuyển dụng:`,
      jobCards: [],
      showChart: true,
    }
  }

  if (t.includes('xu hướng') || t.includes('market') || t.includes('thị trường')) {
    return {
      type: 'text',
      content: `📊 **State of the Market — Q2/2025:**\n\n` +
        `Nhu cầu tuyển dụng kỹ sư Mid-to-Senior tại Việt Nam đã ổn định, với mức tăng đáng kể **+15%** các vị trí yêu cầu AI/ML. ` +
        `Hệ sinh thái JavaScript truyền thống (React/Node) vẫn là driver lớn nhất về volume, ` +
        `nhưng các vai trò backend chuyên sâu (Go, Python) có premium lương trung bình **+12%**.\n\n` +
        `Remote work flexibility tiếp tục là điểm thương lượng chính với top talent.\n\n` +
        `Bạn muốn xem chi tiết phân tích theo thành phố không?`,
      jobCards: [],
      showChart: false,
    }
  }

  // Default: job search intent
  const matchedJobs = MOCK_JOBS.slice(0, 2)
  return {
    type: 'mixed',
    content: `Tôi đã tìm kiếm và lọc từ ${MOCK_JOBS.length} tin tuyển dụng IT. Đây là những vị trí phù hợp nhất với yêu cầu của bạn:`,
    jobCards: matchedJobs,
    showChart: false,
    followUp: `\n\nBạn có muốn tôi giúp viết cover letter cho một trong những vị trí trên không? 😊`,
  }
}

/** FR-10 — Text-to-SQL: turn a natural-language analytics question into chart data. */
export async function textToSqlChart(_question) {
  if (USE_MOCK) { await mockDelay(500); return SKILL_DATA.slice(0, 5) }
  // const { data } = await api.post('/chat/text-to-sql', { question })
  // return data
}

/** FR-11 — RAG company lookup against the vector DB. */
export async function ragCompanyLookup(_companyName) {
  if (USE_MOCK) {
    await mockDelay(400)
    return { source: 'Vector DB', summary: 'Thông tin công ty được trích xuất từ tài liệu nội bộ.' }
  }
  // const { data } = await api.post('/chat/rag-lookup', { company: companyName })
  // return data
}

export const CHAT_WS_URL = WS_URL
