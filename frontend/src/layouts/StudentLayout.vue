<script setup>
import { useRoute, useRouter } from 'vue-router'
import { logout as logoutRequest } from '../api'
import { clearAuthUser, getAuthUser } from '../composables/useAuth'
import UtilityDock from '../components/UtilityDock.vue'
import PillNav from '../components/PillNav.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import SemiIcon from '../components/SemiIcon.vue'

const router = useRouter()
const route = useRoute()
const user = getAuthUser() || {}
const links = [
  { to: '/student/home', label: '首页' },
  { to: '/student/chat', label: '信息问答' },
  { to: '/student/history', label: '问答记录' },
]
const logout = async () => {
  try { await logoutRequest() } catch {}
  clearAuthUser()
  router.push('/login')
}
</script>

<template>
  <div class="student-shell">
    <div v-if="user.role === 'teacher' && route.query.preview === 'teacher'" class="teacher-preview-bar">
      <span><b>教师预览模式</b> 当前正在查看学生端页面</span>
      <RouterLink to="/teacher/dashboard"><SemiIcon name="arrow-left" /> 返回教师后台</RouterLink>
    </div>
    <header class="student-header">
      <RouterLink class="brand" to="/student/home">
        <span class="school-emblem"><i></i><b>知</b></span>
        <span><strong>校园信息问答中台</strong><small>学生服务端</small></span>
      </RouterLink>
      <PillNav :items="links" :teacher-preview="user.role === 'teacher'" />
      <div class="user-menu">
        <RouterLink class="student-account" :to="user.role === 'teacher' ? { path: '/student/profile', query: { preview: 'teacher' } } : '/student/profile'">
          <span class="student-avatar"><SemiIcon name="user" /></span>
          <span><strong>{{ user.displayName }}</strong><small>{{ user.account }}</small></span>
        </RouterLink>
        <i></i>
        <button class="student-logout" type="button" aria-label="退出登录" title="退出登录" @click="logout"><SemiIcon name="exit" /><span>退出</span></button>
        <div class="header-personal-tools">
          <ThemeToggle />
        </div>
      </div>
    </header>
    <main :class="['student-main', { 'is-chat-page': route.path === '/student/chat' }]"><RouterView /></main>
    <UtilityDock />
  </div>
</template>
