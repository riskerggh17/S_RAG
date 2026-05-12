<script setup lang="ts">
import { ref } from 'vue'

// 定义侧边栏折叠状态，false 为展开，true 为折叠
const isCollapsed = ref(false)

// 切换状态的函数
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 处理文本框输入事件
const handleTextareaInput = (event: Event) => {
  const textarea = event.target as HTMLTextAreaElement
  
  // 1. 先重置高度为 auto，让浏览器根据内容重新计算真实高度
  textarea.style.height = 'auto'
  
  // 2. 定义 5 行的最大高度 (假设行高是 24px, 5 * 24 = 120px)
  // 你可以根据实际的 line-height 调整这个值
  const MAX_HEIGHT = 160 
  
  // 3. 如果真实高度小于最大高度，就设为真实高度；否则设为最大高度
  if (textarea.scrollHeight < MAX_HEIGHT) {
    textarea.style.height = `${textarea.scrollHeight}px`
  } else {
    textarea.style.height = `${MAX_HEIGHT}px`
  }
}


</script>

<template>
  <!-- 根容器 -->
  <div class="layout-container" :class="{collapsed: isCollapsed}">
  <!-- 2. 左侧：侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <h2>LOGO</h2>
        <button class="collapse-btn" @click="toggleSidebar">
          <span v-if="!isCollapsed">关闭</span>
        </button>
      </div>
      
      <div class="new-chat">
        <button>新建对话</button>
      </div>
    </aside>



    <!-- 右侧主内容展示区 -->
    <main class="main-content">
      <header class="top-header">
        <!-- 顶部导航栏 -->
        <div class="header-left">
          <button v-if="isCollapsed" class="expand-btn" @click="toggleSidebar">
            展开
          </button>
          <button v-if="isCollapsed" class="new-session-btn" @click="toggleSidebar">
            新会话
          </button>
        </div>
        <div>
          关于
        </div>
      </header>

      <div class="page-body">
        <!-- 这里展示具体的页面内容 -->
        <h1>You did it!</h1>
        <p>这里是右侧主内容区域。</p>
      </div>
      <footer class="footer-input-area">
        <!-- 1文本输入框 -->
        <textarea 
          placeholder="向千问提问..." 
          rows="1"
          @input="handleTextareaInput"
        ></textarea>
        <!-- 2左侧选项组 -->
        <div class="options">
          <span class="opt-item">✨ 任务助理</span>
          <span class="opt-item">🧠 思考</span>
          <span class="opt-item">🔍 研究</span>
          <span class="opt-item">≡ 更多</span>
        </div>
        <!-- 3右侧发送按钮 -->
        <button class="send-btn">
          <span> send </span>
        </button>
      </footer>
    </main>
  </div>
</template>




<style scoped>
/* 根容器：占满全屏，横向排列 */
.layout-container {
  display: flex;
  height: 100vh; /* 视口高度，确保占满屏幕 */
  width: 100vw;  /* 视口宽度 */
  background-color: var(--bg-base); /* 使用全局暗黑背景色 */
  color: var(--text-primary);
  overflow: hidden; /* 防止出现双重滚动条 */
  transition: all 0.3s ease; /* 添加过渡动画 */
}

/* --- 左侧侧边栏 --- */
.sidebar {
  width: calc(100% / 6);
  background-color: var(--bg-surface); /* 使用稍浅的深色背景 */
  border-right: 1px solid #334155; /* 右侧分割线 */
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* 防止窗口缩小时被压缩 */
  transition: all 0.3s ease;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-weight: bold;
  color: var(--color-primary);
}

/* 侧边栏内的折叠按钮样式 */
.collapse-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.2s;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}


.new-chat {
  padding: 16px;
}

.new-chat button {
  /* 布局 */
  width: 100%;
  padding: 10px 0;
  
  /* 视觉样式 */
  background-color: var(--color-primary); /* 使用主色调 (靛蓝色) */
  color: white;
  font-weight: 600;
  font-size: 14px;
  
  /* 边框与圆角 */
  border: none;
  border-radius: 8px; /* 圆润的边角 */
  
  /* 交互 */
  cursor: pointer;
  transition: all 0.2s ease; /* 平滑的过渡动画 */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); /* 轻微阴影 */
}

/* 鼠标悬停效果 */
.new-chat button:hover {
  background-color: var(--color-primary-hover); /* 颜色变深 */
  transform: translateY(-1px); /* 微微上浮 */
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3); /* 发光效果 */
}

/* 鼠标按下效果 */
.new-chat button:active {
  transform: translateY(0);
}


/* --- 右侧主内容区 --- */
.main-content {
  flex: 1; /* 自动占据剩余所有宽度 */
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* 内容过多时，仅右侧出现滚动条 */
  background-color: var(--bg-base);
}

.top-header {
  height: 60px;
  border-bottom: 1px solid #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: var(--bg-surface);
}

/* 顶部左侧：展开按钮和标题 */
.header-left {
  display: flex;
  align-items: center;
  gap: 16px; /* 元素间距 */
}

/* 顶部展开按钮 */
.expand-btn {
  background: transparent;
  border: 1px solid #475569;
  color: var(--text-primary);
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.expand-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

/* 顶部右侧：新会话和头像 */
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 顶部的小新会话按钮 */
.new-session-btn {
  background-color: var(--bg-base);
  color: var(--text-secondary);
  border: 1px solid #334155;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.new-session-btn:hover {
  color: var(--text-primary);
  border-color: var(--color-primary);
  background-color: var(--bg-surface-hover);
}


.page-body {
  padding: 24px;
  flex: 1;
}

/* --- 底部输入区域 --- */
.footer-input-area {
  position: relative;  /* 绝对定位 */
  width: 80%;
  margin: 0 auto 12px auto; /* 底部留白，水平居中 */
  
  background-color: var(--bg-surface);
  border: 1px solid #475569;
  border-radius: 16px;
  padding: 12px 16px;
  font-size: 16px;
  display: flex;
  flex-direction: column; /* 垂直排列：输入框在上，工具栏在下 */
  gap: 4px; /* 输入框与下方工具栏的间距 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  resize: none;
  line-height: 24px;
  max-height: 160px;
  /* 确保内容不会溢出圆角 */
  overflow: hidden; 
}

/* --- 文本输入框 --- */
.footer-input-area textarea {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 16px;
  resize: none; /* 禁止手动拖拽大小，由 rows 控制 */
}



/* --- 左侧选项组 --- */
.options {
  display: flex;
  align-items: center;
  gap: 16px; /* 选项之间的间距 */
}

.options  {
  margin-right: 80px; 
}

.opt-item {
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.opt-item:hover {
  color: var(--text-primary);
}

/* --- 右侧发送按钮 --- */
.send-btn {
  position: absolute; /* 关键：脱离文档流 */
  bottom: 12px;       /* 距离底部 padding */
  right: 12px;        /* 距离右侧 padding */
  
  width: 60px;
  height: 32px;
  background-color: #6366f1; /* 靛蓝色 */
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover {
  background-color: var(--color-primary-hover);
}




/* 当根容器有 .collapsed 类时，修改侧边栏宽度 */
.layout-container.collapsed .sidebar {
  width: 0;
}


</style>
