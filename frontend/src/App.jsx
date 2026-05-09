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

        {/* 新建对话按钮 */}
        <div className="new-chat-container">
          <button className="new-chat-btn">
            <span className="icon">➕</span>
            {isSidebarOpen && <span className="text">新建对话</span>}
          </button>
        </div>

        {/* 历史会话容器 */}
        <div className="history-container">
          <div className="history-header">
            <span>历史会话</span>
          </div>
          <div className="history-list">
            {/* 历史会话列表 - 自动填充 */}
          </div>
        </div>

        {/* 底部用户信息区域 */}
        <div className="sidebar-footer">
          用户头像和id，点击展示设置
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="main-content">
        {/* --- 顶部导航栏 --- */}
        <header className="main-header">
          {/* 1. 展开按钮 (仅在侧边栏折叠时显示) */}
          {!isSidebarOpen && (
            <button className="expand-btn-small" onClick={toggleSidebar}>
              ▶
            </button>
          )}          
          {/* 2. 右侧留空 (flex: 1 会自动处理) */}
        </header>
        {/* --- 原有内容包裹在 wrapper 中 --- */}
        <div className="content-wrapper">
          <div className="display-area">
            <p>这里是主要展示区，内容多了会自动出现滚动条。</p>
          </div>

          {/* 2. 下方：用户输入区（固定在底部） */}
          <div className="input-area">
            <p>这里是用户输入区</p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
