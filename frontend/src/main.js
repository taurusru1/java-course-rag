import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import SemiIcon from './components/SemiIcon.vue'
import './style.css'

createApp(App).use(router).component('SemiIcon', SemiIcon).mount('#app')
