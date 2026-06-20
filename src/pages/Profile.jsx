import { useState } from 'react'
import { Pencil, Plus, X, Upload, Trash2, ExternalLink, Camera } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { useNavigate } from 'react-router-dom'
import {
  Tabs, Card, Button, Input, AIBadge, Avatar,
  ProgressBar, EmptyState,
} from '../components/ui'
import JobCard from '../components/JobCard'
import { SKILL_LEVELS, LEVEL_COLOR } from '../data/mockData'
import clsx from 'clsx'

const PROFILE_TABS = [
  { id: 'info',     label: 'Thông tin cá nhân' },
  { id: 'skills',   label: 'Hồ sơ kỹ năng' },
  { id: 'prefs',    label: 'Career Preferences' },
  { id: 'cv',       label: 'CV của tôi' },
  { id: 'saved',    label: 'Việc đã lưu' },
]

// ── Tab: Personal Info ────────────────────────────────────────────────────────
function TabPersonal({ profile, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm]       = useState(profile)

  const handleSave = () => { onUpdate(form); setEditing(false) }
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div className="lg:col-span-2 space-y-5">
        {/* About */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">About Me</h3>
            <button onClick={() => setEditing(!editing)} className="text-text-muted hover:text-violet transition-colors">
              <Pencil size={13} />
            </button>
          </div>
          {editing ? (
            <textarea
              rows={4}
              className="w-full text-sm text-text-secondary border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:border-violet"
              value={form.about}
              onChange={set('about')}
            />
          ) : (
            <p className="text-sm text-text-secondary leading-relaxed">{profile.about}</p>
          )}
        </Card>

        {/* Personal details */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-4">Personal Details</h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Full Name', key: 'name' },
              { label: 'Date of Birth', key: 'dob' },
              { label: 'Nationality', key: 'nationality' },
              { label: 'Gender', key: 'gender' },
              { label: 'Email', key: 'email' },
              { label: 'Phone', key: 'phone' },
            ].map(({ label, key }) => (
              <div key={key}>
                <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-1">{label}</p>
                {editing
                  ? <input className="w-full text-sm border border-gray-200 rounded px-2 py-1.5 focus:outline-none focus:border-violet" value={form[key] || ''} onChange={set(key)} />
                  : <p className="text-sm text-text-primary">{profile[key]}</p>
                }
              </div>
            ))}
          </div>
          {editing && (
            <div className="flex gap-2 mt-4">
              <Button variant="primary" size="sm" onClick={handleSave}>Lưu thay đổi</Button>
              <Button variant="ghost" size="sm" onClick={() => { setForm(profile); setEditing(false) }}>Huỷ</Button>
            </div>
          )}
        </Card>
      </div>

      {/* AI sidebar */}
      <div className="space-y-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <AIBadge variant="violet">✨ AI Profile Analysis</AIBadge>
          </div>
          <p className="text-xs text-text-secondary mb-3 leading-relaxed">
            Based on your current profile, our AI suggests updating your recent project descriptions to match Senior level requirements.
          </p>
          <Button variant="secondary" size="sm" className="w-full">Analyze Profile</Button>
        </Card>

        <Card className="p-4">
          <h4 className="text-xs font-semibold text-text-primary mb-2">Profile Completeness</h4>
          <div className="flex items-center justify-between mb-1.5">
            <ProgressBar value={profile.completeness} className="flex-1 mr-2" />
            <span className="text-sm font-bold text-mint">{profile.completeness}%</span>
          </div>
          <p className="text-xs text-text-muted">{profile.completenessHint}</p>
        </Card>
      </div>
    </div>
  )
}

// ── Tab: Skills ───────────────────────────────────────────────────────────────
function TabSkills({ profile, onUpdate }) {
  const [skills, setSkills] = useState(profile.skills)
  const [newSkill, setNewSkill] = useState('')
  const [newLevel, setNewLevel] = useState('Beginner')

  const addSkill = () => {
    if (!newSkill.trim()) return
    const updated = [...skills, { name: newSkill.trim(), level: newLevel }]
    setSkills(updated)
    onUpdate({ skills: updated })
    setNewSkill('')
  }

  const removeSkill = (i) => {
    const updated = skills.filter((_, idx) => idx !== i)
    setSkills(updated)
    onUpdate({ skills: updated })
  }

  const cycleLevel = (i) => {
    const curr  = SKILL_LEVELS.indexOf(skills[i].level)
    const next  = SKILL_LEVELS[(curr + 1) % SKILL_LEVELS.length]
    const updated = skills.map((s, idx) => idx === i ? { ...s, level: next } : s)
    setSkills(updated)
    onUpdate({ skills: updated })
  }

  return (
    <Card className="p-5">
      <h3 className="text-sm font-semibold text-text-primary mb-4">Kỹ năng của bạn</h3>
      <div className="flex flex-wrap gap-2 mb-5">
        {skills.map((s, i) => (
          <div key={i} className="flex items-center gap-1.5 bg-gray-50 rounded-full pl-3 pr-1.5 py-1 border border-gray-200">
            <span className="text-xs font-medium text-text-primary">{s.name}</span>
            <button
              onClick={() => cycleLevel(i)}
              className={clsx('text-2xs font-semibold px-1.5 py-0.5 rounded-full transition-colors', LEVEL_COLOR[s.level])}
            >
              {s.level}
            </button>
            <button onClick={() => removeSkill(i)} className="text-text-muted hover:text-red-400 transition-colors p-0.5">
              <X size={10} />
            </button>
          </div>
        ))}
      </div>

      {/* Add new skill */}
      <div className="flex gap-2 items-end">
        <Input
          label="Thêm kỹ năng"
          value={newSkill}
          onChange={e => setNewSkill(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addSkill()}
          placeholder="e.g. Kubernetes, Rust..."
          className="flex-1"
        />
        <select
          value={newLevel}
          onChange={e => setNewLevel(e.target.value)}
          className="text-sm border border-gray-200 rounded px-2 py-2 focus:outline-none focus:border-violet h-9"
        >
          {SKILL_LEVELS.map(l => <option key={l}>{l}</option>)}
        </select>
        <Button variant="primary" size="sm" onClick={addSkill} className="h-9 px-3">
          <Plus size={14} />
        </Button>
      </div>
      <p className="text-xs text-text-muted mt-2">Click vào level để đổi: Beginner → Intermediate → Advanced → Expert</p>
    </Card>
  )
}

// ── Tab: Career Preferences ────────────────────────────────────────────────────
function TabPreferences({ profile, onUpdate }) {
  const [prefs, setPrefs] = useState(profile.preferences)
  const set = k => v => { const p = { ...prefs, [k]: v }; setPrefs(p); onUpdate({ preferences: p }) }

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Vị trí mong muốn</h3>
        <Input
          value={prefs.position}
          onChange={e => set('position')(e.target.value)}
          placeholder="e.g. Senior Frontend Developer"
        />
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Lương kỳ vọng (USD/tháng)</h3>
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-violet w-16">${prefs.salaryMin.toLocaleString()}</span>
          <input type="range" min={300} max={10000} step={100} value={prefs.salaryMin}
            onChange={e => set('salaryMin')(+e.target.value)} className="flex-1" />
          <input type="range" min={300} max={10000} step={100} value={prefs.salaryMax}
            onChange={e => set('salaryMax')(+e.target.value)} className="flex-1" />
          <span className="text-sm font-semibold text-violet w-16 text-right">${prefs.salaryMax.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-xs text-text-muted mt-1">
          <span>Tối thiểu</span><span>Tối đa</span>
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Địa điểm</h3>
        <div className="flex flex-wrap gap-2">
          {['TP.HCM', 'Hà Nội', 'Đà Nẵng', 'Remote'].map(loc => (
            <button
              key={loc}
              onClick={() => set('locations')(
                prefs.locations.includes(loc)
                  ? prefs.locations.filter(l => l !== loc)
                  : [...prefs.locations, loc]
              )}
              className={clsx(
                'px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                prefs.locations.includes(loc)
                  ? 'bg-indigo text-white border-indigo'
                  : 'border-gray-200 text-text-secondary hover:border-indigo hover:text-indigo'
              )}
            >
              {loc}
            </button>
          ))}
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Hình thức làm việc</h3>
        <div className="flex flex-wrap gap-2">
          {['Full-time', 'Part-time', 'Remote', 'Hybrid'].map(t => (
            <button
              key={t}
              onClick={() => set('workTypes')(
                prefs.workTypes.includes(t)
                  ? prefs.workTypes.filter(x => x !== t)
                  : [...prefs.workTypes, t]
              )}
              className={clsx(
                'px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                prefs.workTypes.includes(t)
                  ? 'bg-mint text-white border-mint'
                  : 'border-gray-200 text-text-secondary hover:border-mint hover:text-mint'
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </Card>
    </div>
  )
}

// ── Tab: CV ────────────────────────────────────────────────────────────────────
function TabCV() {
  const [files, setFiles] = useState([
    { name: 'Nguyen_Van_A_CV_2025.pdf', size: '245 KB', active: true, date: '18/06/2025' },
  ])

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">CV đã tải lên</h3>
        {files.map((f, i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 mb-3">
            <div className="w-8 h-8 rounded bg-red-50 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-red-500">PDF</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{f.name}</p>
              <p className="text-xs text-text-secondary">{f.size} · {f.date}</p>
            </div>
            {f.active && <span className="text-xs text-mint font-medium bg-mint-bg px-2 py-0.5 rounded-full">Active</span>}
            <div className="flex gap-1">
              <button className="p-1.5 rounded text-text-muted hover:text-violet transition-colors"><ExternalLink size={13} /></button>
              <button onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}
                className="p-1.5 rounded text-text-muted hover:text-red-400 transition-colors"><Trash2 size={13} /></button>
            </div>
          </div>
        ))}

        <label className="flex items-center justify-center gap-2 w-full p-4 border-2 border-dashed border-gray-200 rounded-lg cursor-pointer hover:border-violet hover:bg-violet-bg/30 transition-all">
          <Upload size={16} className="text-text-muted" />
          <span className="text-sm text-text-secondary">Upload CV mới (PDF, max 10MB)</span>
          <input type="file" accept=".pdf" className="hidden" />
        </label>
      </Card>
    </div>
  )
}

// ── Main Profile page ──────────────────────────────────────────────────────────
export default function Profile() {
  const { profile, updateProfile, savedJobs } = useApp()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('info')

  return (
    <div className="animate-fade-in space-y-5">
      {/* Profile header card */}
      <Card className="p-6">
        <div className="flex items-start gap-5">
          <div className="relative shrink-0">
            <Avatar name={profile.name} size={72} />
            <button className="absolute bottom-0 right-0 w-6 h-6 bg-white rounded-full border border-gray-200 shadow-sm flex items-center justify-center text-text-muted hover:text-violet transition-colors">
              <Camera size={11} />
            </button>
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-text-primary">{profile.name}</h1>
            <p className="text-sm text-violet font-medium mt-0.5">{profile.title}</p>
            <div className="flex flex-wrap gap-4 mt-2 text-xs text-text-secondary">
              <span>✉️ {profile.email}</span>
              <span>📞 {profile.phone}</span>
              <span>📍 {profile.location}</span>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setActiveTab('info')}
          >
            <Pencil size={13} /> Edit Profile
          </Button>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs tabs={PROFILE_TABS} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab content */}
      {activeTab === 'info'   && <TabPersonal profile={profile} onUpdate={updateProfile} />}
      {activeTab === 'skills' && <TabSkills profile={profile} onUpdate={updateProfile} />}
      {activeTab === 'prefs'  && <TabPreferences profile={profile} onUpdate={updateProfile} />}
      {activeTab === 'cv'     && <TabCV />}
      {activeTab === 'saved'  && (
        savedJobs.length === 0
          ? <EmptyState icon="🔖" title="Chưa có việc đã lưu" description="Bookmark các tin tuyển dụng để xem lại sau." action={<Button onClick={() => navigate('/jobs')}>Tìm việc ngay</Button>} />
          : <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {savedJobs.map(j => <JobCard key={j.id} job={j} />)}
            </div>
      )}
    </div>
  )
}
