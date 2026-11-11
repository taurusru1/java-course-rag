<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { clearAuthUser, getAuthUser } from '../composables/useAuth'
import { logout } from '../api'

const router = useRouter()
const user = getAuthUser() || {}
const roleLabel = computed(() => (user.role === 'TEACHER' ? '教师' : '学生'))

async function signOut() {
  try { await logout() } catch { /* token 可能已失效，忽略 */ }
  clearAuthUser()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">J</div>
        <div class="brand-text">
          <b>Java 课程辅导</b>
          <span>RAG TUTORING</span>
        </div>
      </div>

      <nav class="nav">
        <RouterLink to="/chat"><span class="dot" />智能问答</RouterLink>
        <RouterLink to="/courses"><span class="dot" />课程与章节</RouterLink>
        <RouterLink to="/practice"><span class="dot" />练习与错题</RouterLink>
        <RouterLink to="/diagnose"><span class="dot" />报错诊断</RouterLink>
      </nav>

      <div class="sidebar-foot">
        <div class="who">{{ user.displayName || user.account }}</div>
        <div class="role">{{ roleLabel }} · {{ user.account }}</div>
        <button type="button" @click="signOut">退出登录</button>
      </div>
    </aside>

    <main class="main">
      <RouterView />
    </main>
  </div>
</template>
