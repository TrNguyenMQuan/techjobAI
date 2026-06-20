import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Upload, Copy, Download, RefreshCw, FileText, Check, Sparkles } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { MOCK_JOBS } from '../data/mockData'
import { AIBadge, Button, Skeleton } from '../components/ui'

// ─── Mock cover letter generator ─────────────────────────────────────────────
function generateCoverLetter(jobTitle, company, skills) {
  const skillList = skills?.join(', ') || 'React, TypeScript, Node.js'
  return `Hà Nội, ngày ${new Date().toLocaleDateString('vi-VN', { day: 'numeric', month: 'long', year: 'numeric' })}

Kính gửi Ban Tuyển Dụng ${company},

Tôi viết thư này để bày tỏ sự quan tâm mạnh mẽ đến vị trí ${jobTitle} tại ${company}. Qua nghiên cứu về công ty, tôi nhận thấy ${company} đang xây dựng những sản phẩm công nghệ có tầm ảnh hưởng lớn, và tôi mong muốn được đóng góp vào hành trình phát triển đó.

Với hơn 5 năm kinh nghiệm trong lĩnh vực phát triển phần mềm, tôi đã có cơ hội làm việc chuyên sâu với ${skillList}. Những công nghệ này cho phép tôi xây dựng các ứng dụng web có khả năng mở rộng cao, hiệu suất tốt và trải nghiệm người dùng xuất sắc.

Tại công ty trước, tôi đã:
• Dẫn dắt đội nhóm 6 kỹ sư để phát triển lại toàn bộ frontend platform, tăng hiệu suất 40%
• Triển khai CI/CD pipeline giúp rút ngắn thời gian release từ 2 tuần xuống còn 2 ngày
• Mentoring 3 junior developer, trong đó 2 người đã được promote lên mid-level trong 1 năm

Tôi đặc biệt ấn tượng với văn hóa engineering tại ${company} — nơi đề cao chất lượng code, innovation và sự phát triển liên tục của cá nhân. Tôi tin rằng phong cách làm việc chủ động, tư duy systems và kỹ năng giao tiếp của mình sẽ là đóng góp có giá trị cho team.

Tôi rất mong được có cơ hội trao đổi thêm về vị trí này. Cảm ơn quý công ty đã dành thời gian xem xét hồ sơ của tôi.

Trân trọng,
Nguyễn Văn A
nguyenvana@example.com | +84 123 456 789`
}

// ─── CV placeholder panel ─────────────────────────────────────────────────────
function CVPanel({ hasCV, jobId, onUpload, cvName }) {
  const job = MOCK_JOBS.find(j => j.id === jobId)

  if (!hasCV) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="w-16 h-16 rounded-2xl bg-violet-bg flex items-center justify-center mb-4">
          <Upload size={24} className="text-violet" />
        </div>
        <h3 className="text-base font-semibold text-text-primary mb-2">Upload CV của bạn</h3>
        <p className="text-sm text-text-secondary mb-5 max-w-xs">
          Upload file PDF để AI phân tích và tạo cover letter phù hợp với job bạn đang apply.
        </p>
        <label className="cursor-pointer">
          <Button variant="primary">
            <Upload size={13} /> Chọn file PDF
          </Button>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={e => e.target.files?.[0] && onUpload(e.target.files[0])}
          />
        </label>
        <p className="text-xs text-text-muted mt-3">Tối đa 10MB • Chỉ nhận file .pdf</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full p-4">
      {/* CV file info */}
      <div className="flex items-center gap-2 p-2.5 bg-gray-50 rounded-lg border border-gray-200 mb-3">
        <FileText size={16} className="text-violet shrink-0" />
        <span className="text-xs font-medium text-text-primary truncate">{cvName}</span>
      </div>

      {/* Fake PDF preview */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden mb-3">
        <div className="h-full p-4 space-y-2 overflow-y-auto">
          <div className="text-center mb-3">
            <p className="text-sm font-bold text-text-primary">NGUYỄN VĂN A</p>
            <p className="text-xs text-text-secondary">Senior Frontend Developer</p>
            <p className="text-2xs text-text-muted">nguyenvana@example.com • +84 123 456 789 • TP.HCM</p>
          </div>
          {['SUMMARY', 'EXPERIENCE', 'SKILLS', 'EDUCATION'].map(s => (
            <div key={s}>
              <p className="text-xs font-bold text-text-primary border-b border-gray-200 pb-0.5 mb-1">{s}</p>
              <div className="space-y-1">
                <div className="skeleton h-2.5 w-full" />
                <div className="skeleton h-2.5 w-5/6" />
                <div className="skeleton h-2.5 w-4/6" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <label className="text-xs text-violet hover:underline text-left cursor-pointer">
        Upload CV khác
        <input
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={e => e.target.files?.[0] && onUpload(e.target.files[0])}
        />
      </label>

      {/* Job card mini */}
      {job && (
        <div className="mt-3 p-3 bg-violet-bg rounded-lg border border-violet/20">
          <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-1">Đang apply:</p>
          <p className="text-xs font-semibold text-text-primary">{job.title}</p>
          <p className="text-2xs text-text-secondary">{job.company} · {job.location}</p>
        </div>
      )}
    </div>
  )
}

// ─── Main CoverLetter page ────────────────────────────────────────────────────
export default function CoverLetter() {
  const [searchParams]    = useSearchParams()
  const navigate          = useNavigate()
  const { jobs }          = useApp()
  const jobId             = searchParams.get('jobId')
  const job               = jobs.find(j => j.id === jobId)

  const [hasCV, setHasCV]           = useState(true)
  const [cvName, setCvName]         = useState('Nguyen_Van_A_CV_2025.pdf')
  const [generating, setGenerating] = useState(false)
  const [content, setContent]       = useState('')
  const [copied, setCopied]         = useState(false)
  const [generated, setGenerated]   = useState(false)

  const handleUploadCV = (file) => {
    setCvName(file.name)
    setHasCV(true)
  }

  // Auto-generate on first load if job is known
  useEffect(() => {
    if (job && !generated) {
      handleGenerate()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job])

  const handleGenerate = async () => {
    setGenerating(true)
    setContent('')
    await new Promise(r => setTimeout(r, 1200))
    const text = generateCoverLetter(
      job?.title || 'Senior Developer',
      job?.company || 'TechCorp Vietnam',
      job?.requiredSkills || job?.skills
    )

    // Simulate streaming
    const words = text.split(' ')
    let out = ''
    for (let i = 0; i < words.length; i++) {
      await new Promise(r => setTimeout(r, 10))
      out += (i === 0 ? '' : ' ') + words[i]
      setContent(out)
    }
    setGenerating(false)
    setGenerated(true)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = 'cover_letter.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="animate-fade-in h-[calc(100vh-64px)] flex flex-col -m-6">
      {/* Page title bar */}
      <div className="px-6 py-3.5 border-b border-gray-100 bg-white flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-base font-bold text-text-primary">Cover Letter</h1>
          {job && <p className="text-xs text-text-secondary">Đang tạo cho: <span className="text-violet font-medium">{job.title}</span> · {job.company}</p>}
        </div>
        {!jobId && (
          <Button variant="secondary" size="sm" onClick={() => navigate('/jobs')}>
            ← Chọn việc làm
          </Button>
        )}
      </div>

      {/* Split view — stacks vertically on mobile per spec (CV trên, editor dưới) */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-y-auto lg:overflow-hidden">
        {/* CV panel */}
        <div className="w-full lg:w-1/2 border-b lg:border-b-0 lg:border-r border-gray-200 flex flex-col h-[60vh] lg:h-auto shrink-0">
          <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50 shrink-0">
            <p className="text-xs font-semibold text-text-secondary">CV của bạn</p>
          </div>
          <div className="flex-1 overflow-hidden">
            <CVPanel hasCV={hasCV} jobId={jobId} onUpload={handleUploadCV} cvName={cvName} />
          </div>
        </div>

        {/* Cover Letter editor */}
        <div className="w-full lg:w-1/2 flex flex-col min-h-[70vh] lg:min-h-0 lg:flex-1">
          <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex items-center gap-2 shrink-0 flex-wrap">
            <p className="text-xs font-semibold text-text-secondary">Cover Letter</p>
            {generated && (
              <AIBadge variant="yellow">✍️ AI Generated — Hãy chỉnh sửa trước khi gửi</AIBadge>
            )}
          </div>

          {/* Editor */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {generating && !content ? (
              <div className="flex-1 p-5 space-y-3">
                <div className="flex items-center gap-2 text-xs text-text-secondary mb-4">
                  <Sparkles size={14} className="text-violet animate-spin" />
                  AI đang phân tích CV và tạo cover letter...
                </div>
                {Array(8).fill(0).map((_, i) => (
                  <Skeleton key={i} className={`h-3 ${i % 3 === 2 ? 'w-3/4' : 'w-full'}`} />
                ))}
              </div>
            ) : (
              <textarea
                className="flex-1 w-full p-5 text-sm text-text-primary leading-relaxed resize-none
                           focus:outline-none font-mono"
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Cover letter sẽ xuất hiện ở đây sau khi AI tạo xong..."
                style={{ fontFamily: 'Inter, sans-serif' }}
              />
            )}
          </div>

          {/* Action bar */}
          <div className="px-4 py-3 border-t border-gray-100 bg-white flex items-center gap-2 shrink-0">
            <Button
              variant="ghost" size="sm"
              onClick={handleCopy}
              disabled={!content || generating}
            >
              {copied ? <><Check size={13} className="text-mint" /> Đã copy</> : <><Copy size={13} /> Copy</>}
            </Button>
            <Button
              variant="ghost" size="sm"
              onClick={handleDownload}
              disabled={!content || generating}
            >
              <Download size={13} /> Tải TXT
            </Button>
            <div className="flex-1" />
            <Button
              variant="mint" size="sm"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating
                ? <><RefreshCw size={13} className="animate-spin" /> Đang tạo...</>
                : <><Sparkles size={13} /> Tạo lại với AI</>
              }
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
