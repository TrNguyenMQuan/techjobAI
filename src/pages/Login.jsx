import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, LogIn, Loader2 } from 'lucide-react'
import AuthLayout from '../components/AuthLayout'
import { Button, Input } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export default function Login() {
  const [form, setForm]           = useState({ email: '', password: '' })
  const [errors, setErrors]       = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting]   = useState(false)
  const [serverError, setServerError] = useState('')

  const { login } = useAuth()
  const { updateProfile } = useApp()
  const navigate  = useNavigate()
  const location  = useLocation()
  const from      = location.state?.from?.pathname || '/dashboard'

  const set = key => e => {
    setForm(f => ({ ...f, [key]: e.target.value }))
    setErrors(er => ({ ...er, [key]: '' }))
    setServerError('')
  }

  const validate = () => {
    const next = {}
    if (!form.email.trim()) next.email = 'Vui lòng nhập email.'
    else if (!validateEmail(form.email)) next.email = 'Email không hợp lệ.'
    if (!form.password) next.password = 'Vui lòng nhập mật khẩu.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      const user = await login({ email: form.email.trim(), password: form.password })
      updateProfile({ name: user.name, email: user.email })
      navigate(from, { replace: true })
    } catch (err) {
      setServerError(err.message || 'Đăng nhập thất bại. Vui lòng thử lại.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Đăng nhập"
      subtitle="Chào mừng trở lại! Đăng nhập để tiếp tục tìm việc."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {serverError && (
          <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
            {serverError}
          </div>
        )}

        <Input
          label="Email"
          type="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={set('email')}
          error={errors.email}
          autoComplete="email"
        />

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-text-secondary uppercase tracking-wide">
            Mật khẩu
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={form.password}
              onChange={set('password')}
              autoComplete="current-password"
              className={`w-full px-3 py-2 pr-10 text-sm rounded border transition-all
                focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20
                placeholder:text-text-muted
                ${errors.password ? 'border-red-400' : 'border-gray-200'}`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(v => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-red-500">{errors.password}</p>}
        </div>

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" className="rounded border-gray-300 text-indigo focus:ring-violet" />
            <span className="text-text-secondary">Ghi nhớ đăng nhập</span>
          </label>
          <button type="button" className="text-violet hover:text-violet-light transition-colors font-medium">
            Quên mật khẩu?
          </button>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={submitting}
          className="w-full"
        >
          {submitting
            ? <><Loader2 size={16} className="animate-spin" /> Đang đăng nhập...</>
            : <><LogIn size={16} /> Đăng nhập</>
          }
        </Button>
      </form>

      <div className="mt-6 pt-6 border-t border-gray-100 text-center">
        <p className="text-sm text-text-secondary">
          Chưa có tài khoản?{' '}
          <Link to="/register" className="text-violet font-semibold hover:text-violet-light transition-colors">
            Đăng ký ngay
          </Link>
        </p>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-violet-bg border border-violet/20">
        <p className="text-xs text-violet font-medium mb-1">Tài khoản demo</p>
        <p className="text-xs text-text-secondary">
          Email: <span className="font-mono">demo@techjob.ai</span> · Mật khẩu: <span className="font-mono">demo123</span>
        </p>
      </div>
    </AuthLayout>
  )
}
