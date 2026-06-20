// ─── Settings Page ────────────────────────────────────────────────────────────
import { useState }     from 'react'
import { User, Shield, Bell, Bot, Globe, ChevronRight, Save } from 'lucide-react'
import { Card, Button, Input, Toggle, SectionHeader, Avatar } from '../components/ui'
import { useApp } from '../context/AppContext'
import clsx from 'clsx'

const SETTINGS_NAV = [
  { id: 'account',  icon: User,   label: 'Tài khoản' },
  { id: 'security', icon: Shield, label: 'Bảo mật' },
  { id: 'notif',    icon: Bell,   label: 'Thông báo' },
  { id: 'ai',       icon: Bot,    label: 'Tuỳ chọn AI' },
  { id: 'locale',   icon: Globe,  label: 'Ngôn ngữ & Vùng' },
]

function SettingsNav({ active, onChange }) {
  return (
    <div className="w-48 shrink-0">
      <div className="bg-white rounded-lg shadow-card border border-gray-100 overflow-hidden">
        {SETTINGS_NAV.map(item => (
          <button
            key={item.id}
            onClick={() => onChange(item.id)}
            className={clsx(
              'flex items-center justify-between w-full px-4 py-3 text-sm transition-colors border-b border-gray-100 last:border-0',
              active === item.id
                ? 'bg-violet-bg text-violet font-medium'
                : 'text-text-secondary hover:bg-gray-50 hover:text-text-primary'
            )}
          >
            <div className="flex items-center gap-2">
              <item.icon size={14} />
              {item.label}
            </div>
            <ChevronRight size={12} className="text-text-muted" />
          </button>
        ))}
      </div>
    </div>
  )
}

function AccountSettings({ profile }) {
  const [form, setForm] = useState({
    name: profile.name, title: profile.title,
    email: profile.email, phone: profile.phone,
  })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold text-text-primary mb-5">Thông tin cá nhân</h2>

      {/* Avatar */}
      <div className="flex items-center gap-4 mb-6">
        <Avatar name={profile.name} size={64} />
        <div>
          <p className="text-sm font-medium text-text-primary mb-1">Ảnh đại diện</p>
          <p className="text-xs text-text-secondary mb-2">Định dạng JPG, GIF hoặc PNG. Tối đa 2MB.</p>
          <label className="cursor-pointer">
            <Button variant="secondary" size="sm" onClick={() => {}}>Thay đổi ảnh</Button>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input label="Họ và tên"   value={form.name}  onChange={set('name')}  />
        <Input label="Chức danh"   value={form.title} onChange={set('title')} />
        <Input label="Email"       value={form.email} onChange={set('email')} type="email" />
        <Input label="Số điện thoại" value={form.phone} onChange={set('phone')} />
      </div>

      <div className="flex justify-end mt-5">
        <Button variant="primary"><Save size={13} /> Lưu thay đổi</Button>
      </div>
    </Card>
  )
}

function AISettings() {
  const [semanticSearch, setSemanticSearch] = useState(true)
  const [salaryEstimate, setSalaryEstimate] = useState(true)

  return (
    <Card className="p-6 space-y-5">
      <h2 className="text-base font-semibold text-text-primary">Tuỳ chọn AI</h2>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Đề xuất tìm kiếm ngữ nghĩa</p>
            <p className="text-xs text-text-secondary mt-0.5">Sử dụng AI để hiểu ngữ cảnh tìm kiếm.</p>
          </div>
          <Toggle checked={semanticSearch} onChange={setSemanticSearch} />
        </div>
        <div className="border-t border-gray-100 pt-4 flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Ước tính lương AI</p>
            <p className="text-xs text-text-secondary mt-0.5">Hiển thị dự đoán lương dựa trên dữ liệu.</p>
          </div>
          <Toggle checked={salaryEstimate} onChange={setSalaryEstimate} />
        </div>
      </div>
    </Card>
  )
}

function LocaleSettings() {
  return (
    <Card className="p-6 space-y-5">
      <h2 className="text-base font-semibold text-text-primary">Ngôn ngữ & Vùng</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Ngôn ngữ giao diện</p>
          <select className="w-full text-sm border border-gray-200 rounded px-3 py-2 focus:outline-none focus:border-violet">
            <option>Tiếng Việt</option>
            <option>English</option>
          </select>
        </div>
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Múi giờ</p>
          <select className="w-full text-sm border border-gray-200 rounded px-3 py-2 focus:outline-none focus:border-violet">
            <option>(GMT+07:00) Indochina Time – Ho Chi Minh</option>
            <option>(GMT+00:00) UTC</option>
          </select>
        </div>
      </div>
    </Card>
  )
}

export function Settings() {
  const { profile } = useApp()
  const [activeSetting, setActiveSetting] = useState('account')

  return (
    <div className="animate-fade-in space-y-5">
      <SectionHeader title="Cài đặt tài khoản" />
      <div className="flex gap-5 items-start">
        <SettingsNav active={activeSetting} onChange={setActiveSetting} />
        <div className="flex-1">
          {activeSetting === 'account'  && <AccountSettings profile={profile} />}
          {activeSetting === 'ai'       && <AISettings />}
          {activeSetting === 'locale'   && <LocaleSettings />}
          {(activeSetting === 'security' || activeSetting === 'notif') && (
            <Card className="p-8 text-center">
              <p className="text-text-secondary text-sm">
                Tính năng này đang được phát triển.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Help Page ─────────────────────────────────────────────────────────────────
const HELP_CATEGORIES = [
  { icon: '🚀', title: 'Getting Started',     desc: 'Platform basics, setup guide, and initial orientation.' },
  { icon: '🤖', title: 'AI Assistant Tips',   desc: 'Maximize prompt effectiveness and AI cover letter generation.' },
  { icon: '🔍', title: 'Job Search & Filters', desc: 'Understanding semantic search and setting up custom job alerts.' },
  { icon: '📄', title: 'Profile & CV Management', desc: 'Updating your resume, managing privacy, and profile visibility.' },
  { icon: '📊', title: 'Market Insights Explained', desc: 'How to interpret salary data, skill trends, and market graphs.' },
  { icon: '🛡️', title: 'Account & Security',  desc: 'Password resets, data privacy policies, and security settings.' },
]

export function Help() {
  const [search, setSearch] = useState('')

  return (
    <div className="animate-fade-in space-y-5">
      {/* Hero */}
      <div className="bg-indigo rounded-xl p-8 text-center text-white">
        <h1 className="text-2xl font-bold mb-2">How can we help you today?</h1>
        <p className="text-white/70 text-sm mb-5">Search for guides, AI troubleshooting, or account management tutorials.</p>
        <div className="flex items-center gap-2 max-w-lg mx-auto bg-white rounded-lg px-4 py-2.5">
          <span className="text-text-muted">🔍</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search for help, tutorials, or FAQs..."
            className="flex-1 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
          <Button variant="primary" size="sm">Search</Button>
        </div>
      </div>

      {/* Categories */}
      <div>
        <h2 className="text-sm font-semibold text-text-primary mb-4">Browse by Category</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {HELP_CATEGORIES
            .filter(c => !search || c.title.toLowerCase().includes(search.toLowerCase()))
            .map(c => (
              <Card key={c.title} className="p-5 cursor-pointer hover:border-violet/30 hover:shadow-hover transition-all">
                <div className="text-2xl mb-3">{c.icon}</div>
                <h3 className="text-sm font-semibold text-text-primary mb-1">{c.title}</h3>
                <p className="text-xs text-text-secondary leading-relaxed">{c.desc}</p>
              </Card>
            ))}
        </div>
      </div>
    </div>
  )
}
