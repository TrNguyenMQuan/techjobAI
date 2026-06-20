import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-160px)] text-center animate-fade-in">
      <div className="text-7xl mb-4">🛰️</div>
      <h1 className="text-3xl font-bold text-text-primary mb-2">404</h1>
      <p className="text-text-secondary mb-6">Trang bạn tìm không tồn tại hoặc đã được di chuyển.</p>
      <div className="flex gap-3">
        <Button variant="secondary" onClick={() => navigate(-1)}>← Quay lại</Button>
        <Button variant="primary" onClick={() => navigate('/dashboard')}>Về Dashboard</Button>
      </div>
    </div>
  )
}
