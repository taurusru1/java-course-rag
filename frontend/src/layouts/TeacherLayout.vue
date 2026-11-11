<script setup>
import { useRouter } from 'vue-router'
import { logout as logoutRequest } from '../api'
import { clearAuthUser, getAuthUser } from '../composables/useAuth'
import UtilityDock from '../components/UtilityDock.vue'
import ThemeToggle from '../components/ThemeToggle.vue'
import UserProfileCard from '../components/UserProfileCard.vue'

const router = useRouter()
const user = getAuthUser() || {}
const logout = async () => {
  try { await logoutRequest() } catch {}
  clearAuthUser()
  router.push('/login')
}
</script>

<template>
  <div class="teacher-shell">
    <aside class="teacher-sidebar">
      <RouterLink class="teacher-brand" to="/teacher/dashboard"><span class="school-emblem inverse"><i></i><b>知</b></span><div><strong>校园信息问答中台</strong><small>教师管理端</small></div></RouterLink>
      <nav>
        <p>工作台</p>
        <RouterLink to="/teacher/dashboard"><i><SemiIcon name="dashboard" /></i> 数据概览</RouterLink>
        <p>知识库管理</p>
        <RouterLink to="/teacher/knowledge"><i><SemiIcon name="file" /></i> 资料管理</RouterLink>
        <RouterLink to="/teacher/courses"><i><SemiIcon name="book" /></i> 分类与课程</RouterLink>
      </nav>
      <div class="teacher-profile">
        <div class="teacher-profile-identity">
          <span class="teacher-profile-avatar"><SemiIcon name="user" /></span>
          <div><strong>{{ user.displayName }}</strong><small>{{ user.account }}</small></div>
          <span class="teacher-online">在线</span>
        </div>
        <div class="teacher-profile-actions">
          <div class="header-personal-tools teacher-tools"><UserProfileCard /><ThemeToggle /></div>
          <button class="teacher-logout" type="button" @click="logout"><SemiIcon name="exit" />退出登录</button>
        </div>
      </div>
    </aside>
    <section class="teacher-content">
      <header><div><b>教师管理后台</b><small>构建并维护面向学生的校园知识库</small></div><RouterLink :to="{ path: '/student/chat', query: { preview: 'teacher' } }">预览学生端 <SemiIcon name="arrow-right" /></RouterLink></header>
      <main><RouterView /></main>
    </section>
    <UtilityDock />
  </div>
</template>
