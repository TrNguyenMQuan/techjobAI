import { NavLink, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, Search, Bot, TrendingUp, User,
  Settings, HelpCircle, FileText, X,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/dashboard',   icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs',        icon: Search,          label: 'Job Search' },
  { to: '/chat',        icon: Bot,             label: 'AI Assistant' },
  { to: '/market',      icon: TrendingUp,      label: 'Market Insights' },
  { to: '/profile',     icon: User,            label: 'Profile' },
]
const BOTTOM_ITEMS = [
  { to: '/settings', icon: Settings,  label: 'Settings' },
  { to: '/help',     icon: HelpCircle, label: 'Help' },
]

export default function Sidebar({ collapsed, mobileOpen, onMobileClose }) {
  const navigate = useNavigate()

  const SidebarLink = ({ to, icon: Icon, label }) => (
    <NavLink
      to={to}
      end={to === '/dashboard'}
      onClick={mobileOpen ? onMobileClose : undefined}
      className={({ isActive }) =>
        clsx(
          'sidebar-item flex items-center gap-3 px-4 py-2.5 rounded-lg mx-2 cursor-pointer transition-all duration-150 group relative',
          isActive
            ? 'sidebar-active'
            : 'text-white/70 hover:text-white'
        )
      }
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && (
        <span className="text-sm font-medium truncate">{label}</span>
      )}
      {/* Tooltip when collapsed */}
      {collapsed && (
        <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-gray-900 text-white text-xs rounded
                        opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
          {label}
        </div>
      )}
    </NavLink>
  )

  const content = (
    <div className="flex flex-col h-full py-4 overflow-hidden">
      {/* Logo */}
      <div className={clsx('flex items-center gap-3 px-5 mb-6', collapsed && 'justify-center px-0')}>
        <div className="w-8 h-8 rounded-lg bg-violet flex items-center justify-center shrink-0">
          <span className="text-white text-xs font-black">T</span>
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="text-white font-bold text-base leading-tight">TechJob AI</div>
            <div className="text-white/50 text-2xs leading-tight">Intelligent Career Platform</div>
          </div>
        )}
        {mobileOpen && (
          <button onClick={onMobileClose} className="ml-auto text-white/60 hover:text-white p-1">
            <X size={18} />
          </button>
        )}
      </div>

      {/* Cover Letter CTA */}
      {!collapsed && (
        <div className="px-4 mb-5">
          <button
            onClick={() => { navigate('/cover-letter'); if (mobileOpen) onMobileClose?.() }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                       border border-mint text-mint text-xs font-semibold
                       hover:bg-mint hover:text-white transition-all"
          >
            <FileText size={13} />
            Write Cover Letter
          </button>
        </div>
      )}

      {/* Main nav */}
      <nav className="flex flex-col gap-0.5 flex-1">
        {NAV_ITEMS.map(item => <SidebarLink key={item.to} {...item} />)}
      </nav>

      {/* Bottom items */}
      <div className="flex flex-col gap-0.5 pt-4 border-t border-white/10 mt-4">
        {BOTTOM_ITEMS.map(item => <SidebarLink key={item.to} {...item} />)}
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={clsx(
          'hidden lg:flex flex-col bg-sidebar shadow-sidebar fixed top-0 left-0 h-full z-30 transition-all duration-300',
          collapsed ? 'w-16' : 'w-60'
        )}
      >
        {content}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onMobileClose}
          />
          <aside className="absolute left-0 top-0 h-full w-64 bg-sidebar shadow-modal animate-slide-in">
            {content}
          </aside>
        </div>
      )}
    </>
  )
}
