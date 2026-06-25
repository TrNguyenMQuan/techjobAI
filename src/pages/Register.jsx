import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, UserPlus, Loader2 } from 'lucide-react'
import AuthLayout from '../components/AuthLayout'
import { Button, Input } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function PasswordField({ label, value, onChange, error, autoComplete, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-text-secondary uppercase tracking-wide">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          className={`w-full px-3 py-2 pr-10 text-sm rounded border transition-all
            focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20
            placeholder:text-text-muted
            ${error ? 'border-red-400' : 'border-gray-200'}`}
        />
        <button
          type="button"
          onClick={() => setShow(v => !v)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
          tabIndex={-1}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [errors, setErrors]       = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  const { register } = useAuth()
  const { updateProfile } = useApp()
  const navigate = useNavigate()

  const set = key => e => {
    setForm(f => ({ ...f, [key]: e.target.value }))
    setErrors(er => ({ ...er, [key]: '' }))
    setServerError('')
  }

  const validate = () => {
    const next = {}
    if (!form.name.trim()) next.name = 'Vui lòng nhập họ và tên.'
    else if (form.name.trim().length < 2) next.name = 'Họ và tên phải có ít nhất 2 ký tự.'
    if (!form.email.trim()) next.email = 'Vui lòng nhập email.'
    else if (!validateEmail(form.email)) next.email = 'Email không hợp lệ.'
    if (!form.password) next.password = 'Vui lòng nhập mật khẩu.'
    else if (form.password.length < 6) next.password = 'Mật khẩu phải có ít nhất 6 ký tự.'
    if (!form.confirmPassword) next.confirmPassword = 'Vui lòng xác nhận mật khẩu.'
    else if (form.password !== form.confirmPassword) next.confirmPassword = 'Mật khẩu không khớp.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      const user = await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
      })
      updateProfile({ name: user.name, email: user.email })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setServerError(err.message || 'Đăng ký thất bại. Vui lòng thử lại.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Đăng ký"
      subtitle="Tạo tài khoản miễn phí và bắt đầu hành trình tìm việc."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {serverError && (
          <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
            {serverError}
          </div>
        )}

        <Input
          label="Họ và tên"
          type="text"
          placeholder="Nguyễn Văn A"
          value={form.name}
          onChange={set('name')}
          error={errors.name}
          autoComplete="name"
        />

        <Input
          label="Email"
          type="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={set('email')}
          error={errors.email}
          autoComplete="email"
        />

        <PasswordField
          label="Mật khẩu"
          placeholder="Tối thiểu 6 ký tự"
          value={form.password}
          onChange={set('password')}
          error={errors.password}
          autoComplete="new-password"
        />

        <PasswordField
          label="Xác nhận mật khẩu"
          placeholder="Nhập lại mật khẩu"
          value={form.confirmPassword}
          onChange={set('confirmPassword')}
          error={errors.confirmPassword}
          autoComplete="new-password"
        />

        <p className="text-xs text-text-muted leading-relaxed">
          Bằng việc đăng ký, bạn đồng ý với{' '}
          <button type="button" className="text-violet hover:underline">Điều khoản sử dụng</button>
          {' '}và{' '}
          <button type="button" className="text-violet hover:underline">Chính sách bảo mật</button>
          {' '}của TechJob AI.
        </p>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={submitting}
          className="w-full"
        >
          {submitting
            ? <><Loader2 size={16} className="animate-spin" /> Đang tạo tài khoản...</>
            : <><UserPlus size={16} /> Đăng ký</>
          }
        </Button>
      </form>

      <div className="mt-6 pt-6 border-t border-gray-100 text-center">
        <p className="text-sm text-text-secondary">
          Đã có tài khoản?{' '}
          <Link to="/login" className="text-violet font-semibold hover:text-violet-light transition-colors">
            Đăng nhập
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}
