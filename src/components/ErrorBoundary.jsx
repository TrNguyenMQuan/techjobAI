import React from 'react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('React render error:', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="min-h-screen bg-bg flex items-center justify-center p-6">
        <div className="max-w-lg w-full bg-white border border-red-100 shadow-card rounded-xl p-6">
          <p className="text-sm font-semibold text-red-600 mb-2">Ứng dụng đang gặp lỗi render</p>
          <h1 className="text-xl font-bold text-text-primary mb-2">Không thể hiển thị màn hình này</h1>
          <p className="text-sm text-text-secondary mb-4">
            Dev build đã bắt được lỗi thay vì để trang trắng. Hãy mở console để xem chi tiết kỹ thuật.
          </p>
          <pre className="text-xs bg-red-50 text-red-700 rounded-lg p-3 overflow-auto max-h-40 mb-4">
            {this.state.error?.message || String(this.state.error)}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 rounded-lg bg-indigo text-white text-sm font-medium hover:bg-indigo-dark"
          >
            Tải lại trang
          </button>
        </div>
      </div>
    )
  }
}
