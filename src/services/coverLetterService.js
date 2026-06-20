import { api, mockDelay } from './api'

const USE_MOCK = true

/**
 * FR-8 — Generate an AI cover letter for a given job + CV combination.
 * Streaming in the real implementation would come over SSE/WebSocket;
 * the mock version here returns the full text immediately and the UI
 * (`CoverLetter.jsx`) re-creates a streaming effect client-side.
 */
export async function generateCoverLetter({ jobTitle, company, skills }) {
  if (USE_MOCK) {
    await mockDelay(800)
    return {
      content: `Kính gửi Ban Tuyển Dụng ${company},\n\nTôi viết thư này để ứng tuyển vị trí ${jobTitle}...`,
      model: 'mock-gpt-4',
    }
  }
  const { data } = await api.post('/cover-letter/generate', { jobTitle, company, skills })
  return data
}
