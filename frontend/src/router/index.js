import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken, getAuthUser } from '../composables/useAuth'

const routes = [
  { path: '/', redirect: '/chat' },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      { path: 'chat', name: 'chat', component: () => import('../views/Chat.vue') },
      { path: 'courses', name: 'courses', component: () => import('../views/CourseList.vue') },
      { path: 'practice', name: 'practice', component: () => import('../views/Practice.vue') },
      { path: 'diagnose', name: 'diagnose', component: () => import('../views/Diagnose.vue') },
      { path: 'documents', name: 'documents', component: () => import('../views/Documents.vue') },
      { path: 'teacher', name: 'teacher', component: () => import('../views/Teacher.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', component: () => import('../views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(to => {
  if (to.path === '/login') {
    if (getAuthUser() && getAuthToken()) return '/chat'
    return true
  }
  if (!getAuthUser() || !getAuthToken()) return '/login'
  return true
})

export default router
