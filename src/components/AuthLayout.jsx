import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function AuthLayout({ children, title, subtitle }) {
  return (
    <div className="min-h-screen bg-bg flex flex-col">
      {/* Decorative background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-violet/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-mint/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-indigo/5 blur-3xl" />
      </div>

      <div className="relative flex-1 flex flex-col items-center justify-center px-4 py-10">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 mb-8 group">
          <div className="w-10 h-10 rounded-xl bg-indigo flex items-center justify-center shadow-card group-hover:scale-105 transition-transform">
            <span className="text-white text-sm font-black">T</span>
          </div>
          <div>
            <div className="text-text-primary font-bold text-xl leading-tight">TechJob AI</div>
            <div className="text-text-muted text-xs flex items-center gap-1">
              <Sparkles size={10} className="text-violet" />
              Intelligent Career Platform
            </div>
          </div>
        </Link>

        {/* Card */}
        <div className="w-full max-w-md bg-white rounded-2xl shadow-modal border border-gray-100 p-8 animate-fade-in">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
            {subtitle && (
              <p className="text-sm text-text-secondary mt-1.5">{subtitle}</p>
            )}
          </div>
          {children}
        </div>

        <p className="mt-8 text-xs text-text-muted text-center">
          © 2025 TechJob AI · Nền tảng tìm việc IT thông minh
        </p>
      </div>
    </div>
  )
}
