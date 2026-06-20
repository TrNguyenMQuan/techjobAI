import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { Bell, HelpCircle, Menu, Sparkles, Search, Clock, LogOut, User as UserIcon, Settings } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { Avatar } from './ui'

const RECENT_SEARCHES = [
  'ReactJS Senior TP.HCM',
  'Python Data Engineer Remote',
  'NodeJS Backend $2000+',
]

const AI_SUGGESTIONS = [
  '✨ AI jobs requiring LLM experience',
  '✨ Top-paying DevOps roles this month',
]

export default function Header({ sidebarCollapsed, onMenuToggle }) {
  const [query, setQuery]           = useState('')
  const [focused, setFocused]       = useState(false)
  const [showUser, setShowUser]     = useState(false)
  const { notifications, profile }  = useApp()
  const navigate = useNavigate()

  const handleSearch = (q) => {
    const term = q || query
    if (term.trim()) {
      navigate(`/jobs?q=${encodeURIComponent(term.trim())}`)
      setFocused(false)
    }
  }

  const leftPad = sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'

  return (
    <header className={clsx(
      'fixed top-0 right-0 h-16 bg-white border-b border-gray-100 shadow-sm z-20 transition-all duration-300',
      'left-0', leftPad
    )}>
      <div className="flex items-center h-full px-2.5 sm:px-4 gap-1.5 sm:gap-3 max-w-screen-2xl">
        {/* Mobile hamburger */}
        <button
          className="lg:hidden p-2 rounded-lg text-text-secondary hover:bg-gray-100 transition-colors"
          onClick={onMenuToggle}
        >
          <Menu size={20} />
        </button>

        {/* Search bar */}
        <div className="relative flex-1 min-w-0 max-w-xl">
          <div className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-lg border transition-all',
            focused
              ? 'border-violet ring-2 ring-violet/20 bg-white'
              : 'border-gray-200 bg-gray-50 hover:border-gray-300'
          )}>
            <Search size={14} className="text-text-muted shrink-0" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setTimeout(() => setFocused(false), 150)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Semantic job search..."
              className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none min-w-0"
            />
            <button
              onClick={() => handleSearch()}
              className="shrink-0 text-violet hover:text-violet-light transition-colors"
              title="AI Semantic Search"
            >
              <Sparkles size={15} />
            </button>
          </div>

          {/* Dropdown suggestions */}
          {focused && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-modal border border-gray-100 py-2 z-50 animate-float-up">
              <div className="px-3 py-1">
                <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider mb-1">Tìm kiếm gần đây</p>
                {RECENT_SEARCHES.map(s => (
                  <button
                    key={s}
                    onClick={() => { setQuery(s); handleSearch(s) }}
                    className="flex items-center gap-2 w-full text-left px-2 py-1.5 rounded hover:bg-gray-50 text-sm text-text-secondary"
                  >
                    <Clock size={12} className="shrink-0" /> {s}
                  </button>
                ))}
              </div>
              <div className="px-3 py-1 border-t border-gray-100 mt-1">
                <p className="text-2xs font-semibold text-violet uppercase tracking-wider mb-1">AI Gợi ý</p>
                {AI_SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => { setQuery(s); handleSearch(s) }}
                    className="flex items-center gap-2 w-full text-left px-2 py-1.5 rounded hover:bg-violet-bg text-sm text-text-secondary"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-0.5 sm:gap-1 ml-auto shrink-0">
          {/* History — hidden on narrow mobile to save space */}
          <button className="hidden sm:inline-flex p-2 rounded-lg text-text-secondary hover:bg-gray-100 transition-colors relative">
            <Clock size={18} />
          </button>

          {/* Notifications */}
          <button className="p-2 rounded-lg text-text-secondary hover:bg-gray-100 transition-colors relative">
            <Bell size={18} />
            {notifications > 0 && (
              <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 text-white text-2xs rounded-full flex items-center justify-center font-bold leading-none">
                {notifications}
              </span>
            )}
          </button>

          {/* Help — hidden on narrow mobile (still reachable from the sidebar) */}
          <button
            onClick={() => navigate('/help')}
            className="hidden sm:inline-flex p-2 rounded-lg text-text-secondary hover:bg-gray-100 transition-colors"
          >
            <HelpCircle size={18} />
          </button>

          {/* User avatar */}
          <div className="relative ml-0.5 sm:ml-1">
            <button
              onClick={() => setShowUser(!showUser)}
              className="flex items-center gap-2 p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Avatar name={profile.name} size={32} />
            </button>
            {showUser && (
              <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-lg shadow-modal border border-gray-100 py-2 z-50 animate-float-up">
                <div className="px-4 py-2 border-b border-gray-100 mb-1">
                  <p className="text-sm font-semibold text-text-primary truncate">{profile.name}</p>
                  <p className="text-xs text-text-secondary truncate">{profile.email}</p>
                </div>
                <button
                  onClick={() => { navigate('/profile'); setShowUser(false) }}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-text-secondary hover:bg-gray-50 hover:text-text-primary transition-colors"
                >
                  <UserIcon size={14} /> Hồ sơ của tôi
                </button>
                <button
                  onClick={() => { navigate('/settings'); setShowUser(false) }}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-text-secondary hover:bg-gray-50 hover:text-text-primary transition-colors"
                >
                  <Settings size={14} /> Cài đặt
                </button>
                {/* Help — only shown here on mobile since the header icon is hidden */}
                <button
                  onClick={() => { navigate('/help'); setShowUser(false) }}
                  className="sm:hidden flex items-center gap-2 w-full px-4 py-2 text-sm text-text-secondary hover:bg-gray-50 hover:text-text-primary transition-colors"
                >
                  <HelpCircle size={14} /> Trợ giúp
                </button>
                <div className="border-t border-gray-100 mt-1 pt-1">
                  <button className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-500 hover:bg-red-50 transition-colors">
                    <LogOut size={14} /> Đăng xuất
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
