import { useState } from 'react'
import './App.css'

function App() {
  // 控制侧边栏展开/折叠状态
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  // 切换侧边栏状态
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  return (
    <div className="app-container">
      {/* 左侧边栏 */}
      <aside className={`sidebar ${isSidebarOpen ? 'open' : 'collapsed'}`}>
        {/* 侧边栏头部 */}
        <div className="sidebar-header">
          <span className="sidebar-title">S-RAG</span>
          <button className="toggle-btn" onClick={toggleSidebar}>
            {isSidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        <div className="new-chat-container">
          <button className="new-chat-btn">
            <span className="icon">➕</span> {/* 图标 */}
            {isSidebarOpen && <span className="text">新建对话</span>} {/* 文字：折叠时隐藏 */}
          </button>
        </div>
        {/* 侧边栏内容区域 */}
        <div className="sidebar-content">
          {/* 内容预留 */}
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="main-content">
        {/* 展开按钮 - 仅在侧边栏折叠时显示 */}
        {!isSidebarOpen && (
          <button className="expand-btn" onClick={toggleSidebar}>
            ▶
          </button>
        )}
        
        {/* 1. 上方：主要展示区（比如对话记录、AI回复等） */}
        <div className="display-area">
          <p>这里是主要展示区，内容多了会自动出现滚动条。</p>
        </div>

        {/* 2. 下方：用户输入区（固定在底部） */}
        <div className="input-area">
          <p>这里是用户输入区</p>
        </div>
      </main>
    </div>
  )
}

export default App
