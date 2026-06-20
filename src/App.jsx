import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import Dashboard from './pages/Dashboard'
import JobList from './pages/JobList'
import JobDetail from './pages/JobDetail'
import Chat from './pages/Chat'
import CoverLetter from './pages/CoverLetter'
import MarketInsights from './pages/MarketInsights'
import Profile from './pages/Profile'
import { Settings, Help } from './pages/SettingsHelp'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/jobs" element={<JobList />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/cover-letter" element={<CoverLetter />} />
        <Route path="/market" element={<MarketInsights />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/help" element={<Help />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
