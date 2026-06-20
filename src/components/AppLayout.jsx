import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import Sidebar from './Sidebar'
import Header from './Header'

export default function AppLayout() {
  const [collapsed, setCollapsed]     = useState(false)
  const [mobileOpen, setMobileOpen]   = useState(false)
  const location = useLocation()

  // Auto-collapse sidebar on tablet breakpoints (per design spec: < 1280px -> icon-only)
  useEffect(() => {
    const checkWidth = () => {
      setCollapsed(window.innerWidth < 1280 && window.innerWidth >= 1024)
    }
    checkWidth()
    window.addEventListener('resize', checkWidth)
    return () => window.removeEventListener('resize', checkWidth)
  }, [])

  // Close mobile drawer whenever the route changes
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />
      <Header
        sidebarCollapsed={collapsed}
        onMenuToggle={() => setMobileOpen(true)}
      />

      <main
        className={clsx(
          'pt-16 transition-all duration-300 min-h-screen',
          collapsed ? 'lg:pl-16' : 'lg:pl-60'
        )}
      >
        {/* Pages like Chat / Cover Letter cancel this padding with -m-6 to go full-bleed */}
        <div className="max-w-[1280px] mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
