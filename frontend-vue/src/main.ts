import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// 引入全局样式
import './asstets/styles/global.css'

const app = createApp(App)

app.use(createPinia())

app.mount('#app')
