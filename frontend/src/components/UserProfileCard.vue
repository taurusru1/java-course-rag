<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentUser, getStudentProfile } from '../api'
import { getAuthUser, getAuthToken } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const open = ref(false)
const loading = ref(false)
const shell = ref(null)
const authUser = ref(null)
const profile = ref(null)
const pointer = ref({ x: 50, y: 50, rotateX: 0, rotateY: 0 })

const visible = computed(() => route.path !== '/login' && Boolean(authUser.value && getAuthToken()))
const name = computed(() => profile.value?.name || authUser.value?.displayName || '校园用户')
const account = computed(() => profile.value?.studentNo || authUser.value?.account || '')
const roleLabel = computed(() => authUser.value?.role === 'teacher' ? '教师 · 知识库管理员' : [profile.value?.college, profile.value?.major].filter(Boolean).join(' · ') || '在校学生')
const detailLabel = computed(() => authUser.value?.role === 'teacher' ? '教师管理端' : profile.value?.grade || `学生编号 ${authUser.value?.studentId || '—'}`)
const initials = computed(() => name.value.trim().slice(0, 1).toUpperCase())
const cardStyle = computed(() => ({
  '--profile-pointer-x': `${pointer.value.x}%`,
  '--profile-pointer-y': `${pointer.value.y}%`,
  '--profile-rotate-x': `${pointer.value.rotateX}deg`,
  '--profile-rotate-y': `${pointer.value.rotateY}deg`,
  '--profile-shift-x': `${(pointer.value.x - 50) * 0.04}px`,
  '--profile-shift-y': `${(pointer.value.y - 50) * 0.03}px`,
}))

const load = async () => {
  authUser.value = getAuthUser()
  profile.value = null
  if (!authUser.value || !getAuthToken()) return
  loading.value = true
  try {
    authUser.value = (await getCurrentUser()).data.data || authUser.value
    if (authUser.value.role === 'student') {
      profile.value = (await getStudentProfile(authUser.value.studentId || 1)).data.data
    }
  } catch {
    // The authenticated session object remains a valid fallback for the card.
  } finally {
    loading.value = false
  }
}

const trackPointer = event => {
  if (!shell.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const rect = shell.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(100, ((event.clientX - rect.left) / rect.width) * 100))
  const y = Math.max(0, Math.min(100, ((event.clientY - rect.top) / rect.height) * 100))
  pointer.value = { x, y, rotateX: (50 - y) / 8, rotateY: (x - 50) / 7 }
}
const resetTilt = () => { pointer.value = { x: 50, y: 50, rotateX: 0, rotateY: 0 } }
const goToProfile = () => {
  open.value = false
  router.push(authUser.value?.role === 'teacher' ? '/teacher/dashboard' : '/student/profile')
}
const closeOnEscape = event => { if (event.key === 'Escape') open.value = false }

watch(() => route.fullPath, () => { open.value = false; load() }, { immediate: true })
window.addEventListener('keydown', closeOnEscape)
onBeforeUnmount(() => window.removeEventListener('keydown', closeOnEscape))
</script>

<template>
  <div v-if="visible" class="user-profile-dock" :class="{ open, 'is-teacher': authUser?.role === 'teacher' }">
    <Transition name="profile-pop">
      <div v-if="open" class="profile-card-wrap" :style="cardStyle">
        <div class="profile-card-behind"></div>
        <article ref="shell" class="profile-card-shell" @pointermove="trackPointer" @pointerleave="resetTilt">
          <div class="profile-card-surface">
            <div class="profile-card-shine"></div>
            <div class="profile-card-glare"></div>
            <header>
              <span>{{ authUser.role === 'teacher' ? 'FACULTY ID' : 'STUDENT ID' }}</span>
              <i></i>
              <b>校园信息问答中台</b>
            </header>
            <div class="profile-card-portrait"><span><SemiIcon name="user" /></span><small>{{ account }}</small></div>
            <div class="profile-card-name"><h3>{{ name }}</h3><p>{{ roleLabel }}</p></div>
            <dl v-if="authUser.role === 'teacher'" class="profile-card-details">
              <div><dt>登录账号</dt><dd>{{ account }}</dd></div>
              <div><dt>权限范围</dt><dd>知识库建设与管理</dd></div>
              <div><dt>当前状态</dt><dd>{{ loading ? '同步中' : '在线' }}</dd></div>
            </dl>
            <footer>
              <div><span class="profile-mini-avatar"><SemiIcon name="user" /></span><p><b>@{{ account }}</b><small><i></i>{{ loading ? '资料同步中' : '当前在线' }}</small></p></div>
              <button type="button" @click="goToProfile">{{ authUser.role === 'teacher' ? '管理后台' : '个人中心' }}</button>
            </footer>
            <div class="profile-card-meta">{{ detailLabel }}</div>
          </div>
        </article>
      </div>
    </Transition>
    <button class="profile-dock-trigger" type="button" :aria-expanded="open" :aria-label="open ? '收起个人资料' : '查看个人资料'" @click="open = !open">
      <span><SemiIcon name="user" /></span><i></i><small>{{ open ? '收起' : '我的' }}</small>
    </button>
  </div>
</template>
