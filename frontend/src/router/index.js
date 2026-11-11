import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken, getAuthUser } from '../composables/useAuth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  {
    path: '/student',
    component: () => import('../layouts/StudentLayout.vue'),
    children: [
      { path: '', redirect: '/student/home' },
      { path: 'home', name: 'student-home', component: () => import('../views/StudentHome.vue') },
      { path: 'chat', name: 'student-chat', component: () => import('../views/Chat.vue') },
      { path: 'courses', redirect: { path: '/student/chat', query: { focus: 'topics' } } },
      { path: 'history', name: 'student-history', component: () => import('../views/StudentHistory.vue') },
      { path: 'favorites', name: 'student-favorites', component: () => import('../views/StudentFavorites.vue') },
      { path: 'notices', name: 'student-notices', component: () => import('../views/StudentNotices.vue') },
      { path: 'profile', name: 'student-profile', component: () => import('../views/StudentProfile.vue') },
    ],
  },
  {
    path: '/teacher',
    component: () => import('../layouts/TeacherLayout.vue'),
    children: [
      { path: '', redirect: '/teacher/dashboard' },
      { path: 'dashboard', name: 'teacher-dashboard', component: () => import('../views/TeacherDashboard.vue') },
      { path: 'knowledge', name: 'teacher-knowledge', component: () => import('../views/Import.vue') },
      { path: 'courses', name: 'teacher-courses', component: () => import('../views/Courses.vue') },
    ],
  },
  { path: '/chat', redirect: '/student/chat' },
  { path: '/courses', redirect: '/student/courses' },
  { path: '/import', redirect: '/teacher/knowledge' },
  { path: '/:pathMatch(.*)*', component: () => import('../views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// A browser tab can outlive a production rebuild. In that case its lazy-route
// chunk names no longer exist in dist, so Vue Router rejects the navigation.
// Reloading the requested URL fetches the current index and current chunks.
const isStaleChunkError = error => {
  const message = String(error?.message || error)
  return /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk .* failed|ChunkLoadError/i.test(message)
}

router.onError((error, to) => {
  if (!isStaleChunkError(error)) return
  const target = router.resolve(to).href
  if (window.location.pathname + window.location.search + window.location.hash === target) {
    window.location.reload()
    return
  }
  window.location.assign(target)
})

router.beforeEach(to => {
  const user = getAuthUser()
  if (to.path === '/login') {
    if (user && getAuthToken()) return user.role === 'teacher' ? '/teacher/dashboard' : '/student/chat'
    return true
  }
  if (!user || !getAuthToken()) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.path.startsWith('/teacher') && user.role !== 'teacher') return '/student/chat'
  if (to.path.startsWith('/student') && user.role !== 'student' && to.query.preview !== 'teacher') return '/teacher/dashboard'
  return true
})

export default router
