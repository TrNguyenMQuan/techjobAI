import clsx from 'clsx'

// ─── AI Badge ───────────────────────────────────────────────────────────────
export function AIBadge({ children, variant = 'mint', className }) {
  const variants = {
    mint:   'bg-mint-bg text-mint-dark border border-mint/30',
    violet: 'bg-violet-bg text-violet border border-violet/30',
    yellow: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
    gray:   'bg-gray-100 text-gray-600 border border-gray-200',
  }
  return (
    <span className={clsx('ai-badge', variants[variant], className)}>
      {children}
    </span>
  )
}

// ─── Tag / Skill chip ───────────────────────────────────────────────────────
export function SkillTag({ children, variant = 'required', className }) {
  const variants = {
    required:  'bg-violet-bg text-violet',
    preferred: 'bg-gray-100 text-gray-600',
    plain:     'bg-indigo/10 text-indigo',
  }
  return (
    <span className={clsx(
      'inline-block text-xs font-medium px-2.5 py-1 rounded-full',
      variants[variant], className
    )}>
      {children}
    </span>
  )
}

// ─── Level badge ────────────────────────────────────────────────────────────
export function LevelBadge({ level }) {
  const map = {
    Junior:      'bg-blue-50 text-blue-600',
    'Mid-Level': 'bg-indigo/10 text-indigo',
    Mid:         'bg-indigo/10 text-indigo',
    Senior:      'bg-violet-bg text-violet',
    Lead:        'bg-amber-50 text-amber-700',
  }
  return (
    <span className={clsx(
      'text-xs font-semibold px-2.5 py-0.5 rounded-full',
      map[level] || 'bg-gray-100 text-gray-600'
    )}>
      {level}
    </span>
  )
}

// ─── Button ─────────────────────────────────────────────────────────────────
export function Button({
  children, variant = 'primary', size = 'md',
  className, disabled, onClick, type = 'button', ...props
}) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-violet'
  const variants = {
    primary:   'bg-indigo text-white hover:bg-indigo-dark active:scale-95',
    secondary: 'bg-white text-indigo border border-indigo/30 hover:bg-violet-bg',
    ghost:     'text-text-secondary hover:bg-gray-100 hover:text-text-primary',
    danger:    'bg-red-500 text-white hover:bg-red-600',
    outline:   'border border-mint text-mint hover:bg-mint-bg',
    mint:      'bg-mint text-white hover:bg-mint-dark active:scale-95',
  }
  const sizes = {
    xs: 'text-xs px-2.5 py-1',
    sm: 'text-xs px-3 py-1.5',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-5 py-2.5',
  }
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={clsx(
        base,
        variants[variant],
        sizes[size],
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

// ─── Skeleton block ──────────────────────────────────────────────────────────
export function Skeleton({ className }) {
  return <div className={clsx('skeleton', className)} />
}

// ─── Card container ──────────────────────────────────────────────────────────
export function Card({ children, className, onClick }) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-white rounded-lg shadow-card border border-gray-100',
        onClick && 'cursor-pointer',
        className
      )}
    >
      {children}
    </div>
  )
}

// ─── Section header ──────────────────────────────────────────────────────────
export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-5">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
        {subtitle && <p className="text-sm text-text-secondary mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

// ─── Empty state ─────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-5xl mb-4 opacity-40">{icon || '📭'}</div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
      {description && <p className="text-sm text-text-secondary max-w-xs mb-5">{description}</p>}
      {action}
    </div>
  )
}

// ─── Input ───────────────────────────────────────────────────────────────────
export function Input({ className, label, error, ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs font-medium text-text-secondary uppercase tracking-wide">{label}</label>}
      <input
        className={clsx(
          'w-full px-3 py-2 text-sm rounded border border-gray-200',
          'focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20',
          'placeholder:text-text-muted transition-all',
          error && 'border-red-400',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}

// ─── Select ──────────────────────────────────────────────────────────────────
export function Select({ className, label, children, ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-xs font-medium text-text-secondary uppercase tracking-wide">{label}</label>}
      <select
        className={clsx(
          'w-full px-3 py-2 text-sm rounded border border-gray-200 bg-white',
          'focus:outline-none focus:border-violet focus:ring-2 focus:ring-violet/20',
          'transition-all cursor-pointer',
          className
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  )
}

// ─── Avatar ──────────────────────────────────────────────────────────────────
export function Avatar({ name, src, size = 32 }) {
  const initials = name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'
  if (src) {
    return <img src={src} alt={name} className="rounded-full object-cover" style={{ width: size, height: size }} />
  }
  return (
    <div
      className="rounded-full bg-indigo text-white font-semibold flex items-center justify-center select-none"
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials}
    </div>
  )
}

// ─── Tabs ────────────────────────────────────────────────────────────────────
export function Tabs({ tabs, activeTab, onTabChange }) {
  return (
    <div className="flex border-b border-gray-200 mb-6">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={clsx(
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px',
            activeTab === tab.id
              ? 'border-violet text-violet'
              : 'border-transparent text-text-secondary hover:text-text-primary hover:border-gray-300'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

// ─── Toggle switch ───────────────────────────────────────────────────────────
export function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer select-none">
      <div className="relative">
        <input type="checkbox" className="sr-only" checked={checked} onChange={e => onChange(e.target.checked)} />
        <div className={clsx(
          'w-10 h-6 rounded-full transition-colors',
          checked ? 'bg-mint' : 'bg-gray-300'
        )} />
        <div className={clsx(
          'absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-4' : 'translate-x-0'
        )} />
      </div>
      {label && <span className="text-sm text-text-primary">{label}</span>}
    </label>
  )
}

// ─── Progress bar ────────────────────────────────────────────────────────────
export function ProgressBar({ value, max = 100, color = 'bg-mint', className }) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  return (
    <div className={clsx('w-full h-2 bg-gray-100 rounded-full overflow-hidden', className)}>
      <div className={clsx('h-full rounded-full transition-all duration-500', color)} style={{ width: `${pct}%` }} />
    </div>
  )
}

// ─── Typing indicator ───────────────────────────────────────────────────────
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0,1,2].map(i => (
        <div
          key={i}
          className="w-2 h-2 rounded-full bg-text-muted typing-dot animate-typing-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  )
}
