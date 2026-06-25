// ─── Settings Page ────────────────────────────────────────────────────────────
import { useState }     from 'react'
import { User, Shield, Bell, Bot, Globe, ChevronRight, Save, Check, Lock, Eye, EyeOff } from 'lucide-react'
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

// ── Account Settings ─────────────────────────────────────────────────────────
function AccountSettings({ profile, updateProfile }) {
  const [form, setForm] = useState({
    name: profile.name, title: profile.title,
    email: profile.email, phone: profile.phone,
  })
  const [saved, setSaved] = useState(false)
  const set = k => e => { setForm(f => ({ ...f, [k]: e.target.value })); setSaved(false) }

  const handleSave = () => {
    updateProfile(form)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

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

      <div className="flex items-center justify-end gap-3 mt-5">
        {saved && (
          <span className="flex items-center gap-1 text-xs text-mint font-medium animate-fade-in">
            <Check size={13} /> Đã lưu thành công
          </span>
        )}
        <Button variant="primary" onClick={handleSave}><Save size={13} /> Lưu thay đổi</Button>
      </div>
    </Card>
  )
}

// ── Security Settings ─────────────────────────────────────────────────────────
function SecuritySettings() {
  const [form, setForm] = useState({ current: '', newPass: '', confirm: '' })
  const [show, setShow] = useState({ current: false, newPass: false, confirm: false })
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const set = k => e => { setForm(f => ({ ...f, [k]: e.target.value })); setError(''); setSaved(false) }
  const toggle = k => setShow(s => ({ ...s, [k]: !s[k] }))

  const handleSave = () => {
    if (!form.current) { setError('Vui lòng nhập mật khẩu hiện tại.'); return }
    if (form.newPass.length < 6) { setError('Mật khẩu mới phải có ít nhất 6 ký tự.'); return }
    if (form.newPass !== form.confirm) { setError('Xác nhận mật khẩu không khớp.'); return }

    // Update password in mock user store
    const token = localStorage.getItem('techjob_token')
    const usersRaw = localStorage.getItem('techjob_mock_users')
    if (token && usersRaw) {
      const userId = token.startsWith('mock_') ? token.split('_')[1] : null
      if (userId) {
        const users = JSON.parse(usersRaw)
        const idx = users.findIndex(u => u.id === userId)
        if (idx !== -1) {
          if (users[idx].password !== form.current) {
            setError('Mật khẩu hiện tại không đúng.'); return
          }
          users[idx].password = form.newPass
          localStorage.setItem('techjob_mock_users', JSON.stringify(users))
        }
      }
    }

    setSaved(true)
    setForm({ current: '', newPass: '', confirm: '' })
    setTimeout(() => setSaved(false), 2500)
  }

  const PasswordInput = ({ label, field }) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-text-secondary uppercase tracking-wide">{label}</label>
      <div className="relative">
        <input
          type={show[field] ? 'text' : 'password'}
          value={form[field]}
          onChange={set(field)}
          placeholder="••••••••"
          className="w-full px-3 py-2 pr-10 text-sm rounded border border-gray-200 focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20 transition-all"
        />
        <button
          type="button" tabIndex={-1}
          onClick={() => toggle(field)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
        >
          {show[field] ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
    </div>
  )

  return (
    <Card className="p-6 space-y-5">
      <div className="flex items-center gap-2">
        <Lock size={16} className="text-violet" />
        <h2 className="text-base font-semibold text-text-primary">Đổi mật khẩu</h2>
      </div>

      {error && (
        <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
      )}
      {saved && (
        <div className="px-3 py-2.5 rounded-lg bg-mint-bg border border-mint/30 text-sm text-mint-dark flex items-center gap-1.5">
          <Check size={14} /> Mật khẩu đã được cập nhật thành công.
        </div>
      )}

      <div className="space-y-4 max-w-md">
        <PasswordInput label="Mật khẩu hiện tại" field="current" />
        <PasswordInput label="Mật khẩu mới" field="newPass" />
        <PasswordInput label="Xác nhận mật khẩu mới" field="confirm" />
      </div>

      <div className="flex justify-end">
        <Button variant="primary" onClick={handleSave}><Save size={13} /> Cập nhật mật khẩu</Button>
      </div>
    </Card>
  )
}

// ── Notification Settings ─────────────────────────────────────────────────────
function NotificationSettings({ settings, updateSettings }) {
  return (
    <Card className="p-6 space-y-5">
      <h2 className="text-base font-semibold text-text-primary">Cài đặt thông báo</h2>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Thông báo qua email</p>
            <p className="text-xs text-text-secondary mt-0.5">Nhận email khi có hoạt động quan trọng.</p>
          </div>
          <Toggle checked={settings.notifEmail} onChange={v => updateSettings({ notifEmail: v })} />
        </div>
        <div className="border-t border-gray-100 pt-4 flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Job Alert</p>
            <p className="text-xs text-text-secondary mt-0.5">Nhận thông báo khi có việc làm mới phù hợp.</p>
          </div>
          <Toggle checked={settings.notifJobAlert} onChange={v => updateSettings({ notifJobAlert: v })} />
        </div>
        <div className="border-t border-gray-100 pt-4 flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Báo cáo tuần</p>
            <p className="text-xs text-text-secondary mt-0.5">Nhận tổng hợp thị trường IT hàng tuần.</p>
          </div>
          <Toggle checked={settings.notifWeekly} onChange={v => updateSettings({ notifWeekly: v })} />
        </div>
      </div>
    </Card>
  )
}

// ── AI Settings ───────────────────────────────────────────────────────────────
function AISettings({ settings, updateSettings }) {
  return (
    <Card className="p-6 space-y-5">
      <h2 className="text-base font-semibold text-text-primary">Tuỳ chọn AI</h2>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Đề xuất tìm kiếm ngữ nghĩa</p>
            <p className="text-xs text-text-secondary mt-0.5">Sử dụng AI để hiểu ngữ cảnh tìm kiếm.</p>
          </div>
          <Toggle checked={settings.semanticSearch} onChange={v => updateSettings({ semanticSearch: v })} />
        </div>
        <div className="border-t border-gray-100 pt-4 flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-text-primary">Ước tính lương AI</p>
            <p className="text-xs text-text-secondary mt-0.5">Hiển thị dự đoán lương dựa trên dữ liệu.</p>
          </div>
          <Toggle checked={settings.salaryEstimate} onChange={v => updateSettings({ salaryEstimate: v })} />
        </div>
      </div>
    </Card>
  )
}

// ── Locale Settings ──────────────────────────────────────────────────────────
function LocaleSettings({ settings, updateSettings }) {
  return (
    <Card className="p-6 space-y-5">
      <h2 className="text-base font-semibold text-text-primary">Ngôn ngữ & Vùng</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Ngôn ngữ giao diện</p>
          <select
            value={settings.language}
            onChange={e => updateSettings({ language: e.target.value })}
            className="w-full text-sm border border-gray-200 rounded px-3 py-2 focus:outline-none focus:border-violet"
          >
            <option value="vi">Tiếng Việt</option>
            <option value="en">English</option>
          </select>
        </div>
        <div>
          <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Múi giờ</p>
          <select
            value={settings.timezone}
            onChange={e => updateSettings({ timezone: e.target.value })}
            className="w-full text-sm border border-gray-200 rounded px-3 py-2 focus:outline-none focus:border-violet"
          >
            <option value="Asia/Ho_Chi_Minh">(GMT+07:00) Indochina Time – Ho Chi Minh</option>
            <option value="UTC">(GMT+00:00) UTC</option>
            <option value="Asia/Tokyo">(GMT+09:00) Japan Standard Time – Tokyo</option>
            <option value="America/New_York">(GMT-05:00) Eastern Time – New York</option>
          </select>
        </div>
      </div>
    </Card>
  )
}

// ── Main Settings page ───────────────────────────────────────────────────────
export function Settings() {
  const { profile, updateProfile, settings, updateSettings } = useApp()
  const [activeSetting, setActiveSetting] = useState('account')

  return (
    <div className="animate-fade-in space-y-5">
      <SectionHeader title="Cài đặt tài khoản" />
      <div className="flex gap-5 items-start">
        <SettingsNav active={activeSetting} onChange={setActiveSetting} />
        <div className="flex-1">
          {activeSetting === 'account'  && <AccountSettings profile={profile} updateProfile={updateProfile} />}
          {activeSetting === 'security' && <SecuritySettings />}
          {activeSetting === 'notif'    && <NotificationSettings settings={settings} updateSettings={updateSettings} />}
          {activeSetting === 'ai'       && <AISettings settings={settings} updateSettings={updateSettings} />}
          {activeSetting === 'locale'   && <LocaleSettings settings={settings} updateSettings={updateSettings} />}
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
