import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight, Briefcase, CheckCircle2, Facebook, Github, Globe,
  Linkedin, MapPin, Phone, UserRound,
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { Button, Card, Input, Avatar } from '../components/ui'

const SOCIAL_FIELDS = [
  { key: 'facebook', label: 'Facebook', placeholder: 'https://facebook.com/your.name', Icon: Facebook },
  { key: 'github', label: 'GitHub', placeholder: 'https://github.com/username', Icon: Github },
  { key: 'linkedin', label: 'LinkedIn', placeholder: 'https://linkedin.com/in/username', Icon: Linkedin },
  { key: 'website', label: 'Portfolio', placeholder: 'https://your-portfolio.dev', Icon: Globe },
]

const EMPTY_LINKS = {
  facebook: '',
  github: '',
  linkedin: '',
  website: '',
}

function normalizeUrl(value) {
  const trimmed = value?.trim() || ''
  if (!trimmed) return ''
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
}

export default function Onboarding() {
  const { profile, profileReady, updateProfile } = useApp()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    title: '',
    email: '',
    phone: '',
    location: '',
    about: '',
    socialLinks: EMPTY_LINKS,
  })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (!profileReady) return
    if (profile.onboardingCompleted) {
      navigate('/dashboard', { replace: true })
      return
    }
    setForm({
      name: profile.name || '',
      title: profile.title || '',
      email: profile.email || '',
      phone: profile.phone || '',
      location: profile.location || '',
      about: profile.about || '',
      socialLinks: { ...EMPTY_LINKS, ...(profile.socialLinks || {}) },
    })
  }, [navigate, profile, profileReady])

  const set = key => e => {
    setForm(prev => ({ ...prev, [key]: e.target.value }))
    setErrors(prev => ({ ...prev, [key]: '' }))
  }

  const setSocial = key => e => {
    setForm(prev => ({
      ...prev,
      socialLinks: { ...prev.socialLinks, [key]: e.target.value },
    }))
  }

  const validate = () => {
    const next = {}
    if (!form.name.trim()) next.name = 'Vui lòng nhập họ và tên.'
    if (!form.title.trim()) next.title = 'Vui lòng nhập chức danh hoặc vị trí mong muốn.'
    if (!form.phone.trim()) next.phone = 'Vui lòng nhập số điện thoại.'
    if (!form.location.trim()) next.location = 'Vui lòng nhập địa điểm hiện tại.'
    if (form.about.trim().length < 40) next.about = 'Giới thiệu bản thân nên có ít nhất 40 ký tự.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = e => {
    e.preventDefault()
    if (!validate()) return

    const socialLinks = Object.entries(form.socialLinks).reduce((acc, [key, value]) => {
      acc[key] = normalizeUrl(value)
      return acc
    }, {})

    updateProfile({
      name: form.name.trim(),
      title: form.title.trim(),
      phone: form.phone.trim(),
      location: form.location.trim(),
      about: form.about.trim(),
      socialLinks,
      onboardingCompleted: true,
      completeness: 70,
      completenessHint: 'Add skills, CV, and career preferences to reach 100%',
    })
    navigate('/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
        <Card className="p-6 !bg-sidebar text-white !border-white/10 shadow-sidebar">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-lg bg-violet flex items-center justify-center text-sm font-black">T</div>
            <div>
              <p className="text-base font-bold leading-tight">TechJob AI</p>
              <p className="text-xs text-white/55">Profile setup</p>
            </div>
          </div>

          <div className="flex flex-col items-center text-center mb-8">
            <Avatar name={form.name || profile.name} size={86} />
            <h1 className="text-xl font-bold mt-4">Hoàn thiện hồ sơ</h1>
            <p className="text-sm text-white/65 mt-2 leading-relaxed">
              Thông tin này giúp hồ sơ của bạn trông rõ ràng hơn trước khi vào trang chính.
            </p>
          </div>

          <div className="space-y-3 text-sm">
            {[
              'Tên hiển thị đúng với tài khoản đăng ký',
              'Thông tin liên hệ sẵn sàng cho nhà tuyển dụng',
              'Có thể bổ sung GitHub, LinkedIn hoặc portfolio',
            ].map(item => (
              <div key={item} className="flex items-start gap-2 text-white/75">
                <CheckCircle2 size={15} className="text-mint mt-0.5 shrink-0" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <div className="mb-5">
            <h2 className="text-xl font-bold text-text-primary">Thông tin cá nhân</h2>
            <p className="text-sm text-text-secondary mt-1">
              Điền nhanh các trường cần thiết. Bạn vẫn có thể chỉnh sửa lại trong Profile sau.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Họ và tên"
                value={form.name}
                onChange={set('name')}
                error={errors.name}
                placeholder="Nguyễn Văn A"
              />
              <Input
                label="Email đăng nhập"
                value={form.email}
                readOnly
                className="bg-gray-50 text-text-secondary"
              />
              <div className="relative">
                <Input
                  label="Chức danh / vị trí mong muốn"
                  value={form.title}
                  onChange={set('title')}
                  error={errors.title}
                  placeholder="Senior Frontend Developer"
                  className="pl-9"
                />
                <Briefcase size={14} className="absolute left-3 top-[34px] text-text-muted" />
              </div>
              <div className="relative">
                <Input
                  label="Số điện thoại"
                  value={form.phone}
                  onChange={set('phone')}
                  error={errors.phone}
                  placeholder="+84 123 456 789"
                  className="pl-9"
                />
                <Phone size={14} className="absolute left-3 top-[34px] text-text-muted" />
              </div>
              <div className="relative md:col-span-2">
                <Input
                  label="Địa điểm hiện tại"
                  value={form.location}
                  onChange={set('location')}
                  error={errors.location}
                  placeholder="Ho Chi Minh City, VN"
                  className="pl-9"
                />
                <MapPin size={14} className="absolute left-3 top-[34px] text-text-muted" />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary uppercase tracking-wide flex items-center gap-1.5 mb-1">
                <UserRound size={13} /> About Me
              </label>
              <textarea
                rows={4}
                value={form.about}
                onChange={set('about')}
                placeholder="Giới thiệu ngắn về kinh nghiệm, điểm mạnh, định hướng nghề nghiệp..."
                className="w-full text-sm text-text-secondary border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20"
              />
              {errors.about && <p className="text-xs text-red-500 mt-1">{errors.about}</p>}
            </div>

            <div>
              <p className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-2">Social links</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {SOCIAL_FIELDS.map(({ key, label, placeholder, Icon }) => (
                  <label key={key} className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 focus-within:border-violet focus-within:ring-2 focus-within:ring-violet/20 transition-all">
                    <Icon size={15} className="text-text-muted shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider">{label}</p>
                      <input
                        value={form.socialLinks[key]}
                        onChange={setSocial(key)}
                        placeholder={placeholder}
                        className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                      />
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button type="submit" variant="primary" size="lg">
                Hoàn tất hồ sơ <ArrowRight size={16} />
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
