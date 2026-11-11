<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api'
import { setAuthSession } from '../composables/useAuth'
import LightRays from '../components/LightRays.vue'
const router = useRouter()
const route = useRoute()
const role = ref('student')
const account = ref('')
const password = ref('')
const activeField = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const eyeX = ref(0)
const eyeY = ref(0)
const submit = async () => {
  errorMessage.value = ''
  if (!account.value.trim() || !password.value) {
    errorMessage.value = '请输入学号/工号和密码'
    return
  }
  loading.value = true
  try {
    const { data } = await login({ account: account.value.trim(), password: password.value, role: role.value })
    setAuthSession(data.data.token, data.data.user)
    const fallback = role.value === 'student' ? '/student/chat' : '/teacher/dashboard'
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : fallback
    router.replace(redirect.startsWith(`/${role.value}`) ? redirect : fallback)
  } catch (error) {
    errorMessage.value = error.response?.data?.message || '登录服务暂时不可用，请稍后重试'
  } finally {
    loading.value = false
  }
}
const trackPointer = (event) => {
  const rect = event.currentTarget.getBoundingClientRect()
  eyeX.value = Math.max(-1, Math.min(1, (event.clientX - rect.left) / rect.width * 2 - 1)) * 8
  eyeY.value = Math.max(-1, Math.min(1, (event.clientY - rect.top) / rect.height * 2 - 1)) * 6
}
const resetPointer = () => {
  eyeX.value = 0
  eyeY.value = 0
}
</script>

<template>
  <main class="login-page">
    <section class="login-intro" @mousemove="trackPointer" @mouseleave="resetPointer">
      <LightRays
        class="login-light-rays"
        rays-origin="top-right"
        rays-color="#8fc7ff"
        :rays-speed="0.72"
        :light-spread="0.88"
        :ray-length="1.45"
        :fade-distance="1.15"
        :saturation="0.82"
        :follow-mouse="true"
        :mouse-influence="0.12"
        :noise-amount="0.025"
        :distortion="0.035"
      />
      <div class="login-brand"><span class="school-emblem"><i></i><b>知</b></span><div><strong>校园信息问答中台</strong><small>校内信息服务系统</small></div></div>
      <div class="intro-copy">
        <span class="eyebrow light">校内统一信息服务</span>
        <h1>校园信息查询<br />与知识服务平台</h1>
        <p>汇集课程资料、办事指南、规章制度和校园生活信息，为在校师生提供统一、可信的信息查询入口。</p>
        <div class="intro-scope"><span>课程教学</span><span>学生事务</span><span>校园服务</span><span>规章制度</span></div>
      </div>
      <div
        :class="['library-scene', `is-${activeField || 'idle'}`, { 'is-visible': showPassword }]"
        :style="{
          '--eye-x': `${eyeX}px`,
          '--eye-y': `${eyeY}px`,
          '--scene-x': `${eyeX * 1.8}px`,
          '--scene-y': `${eyeY * 1.3}px`,
          '--scene-rotate': `${eyeX * 0.45}deg`,
        }"
      >
        <div class="scene-board">
          <span>校内知识库</span>
          <b>资料已更新至 2026-06-18</b>
          <i></i><i></i><i></i>
        </div>
        <div class="scene-shelf"></div>
        <div class="book-character book-one">
          <div class="book-spine">学生手册</div>
          <div class="character-face"><i class="eye left"></i><i class="eye right"></i><span class="mouth"></span></div>
          <i class="arm arm-left"></i><i class="arm arm-right"></i>
        </div>
        <div class="book-character book-two">
          <div class="book-spine">办事指南</div>
          <div class="character-face"><i class="eye left"></i><i class="eye right"></i><span class="mouth"></span></div>
          <i class="arm arm-left"></i><i class="arm arm-right"></i>
        </div>
        <div class="book-character book-three">
          <div class="book-spine">课程资料</div>
          <div class="character-face"><i class="eye left"></i><i class="eye right"></i><span class="mouth"></span></div>
          <i class="arm arm-left"></i><i class="arm arm-right"></i>
        </div>
        <div class="scene-note">{{ activeField === 'password' ? (showPassword ? '请确认周围环境安全' : '密码输入已保护') : activeField === 'account' ? '正在识别你的校内身份' : '校内资料已准备就绪' }}</div>
      </div>
      <div class="intro-stats"><div><b>权威</b><span>校内资料来源</span></div><div><b>便捷</b><span>统一查询入口</span></div><div><b>清晰</b><span>答案标明依据</span></div></div>
    </section>
    <section class="login-panel">
      <form class="login-card" @submit.prevent="submit">
        <div><span class="eyebrow">用户登录</span><h2>校园信息问答中台</h2><p>请选择身份并使用校内账号登录</p></div>
        <div class="role-tabs"><button type="button" :class="{ active: role === 'student' }" @click="role = 'student'"><b>学生端</b><small>查询信息、智能问答</small></button><button type="button" :class="{ active: role === 'teacher' }" @click="role = 'teacher'"><b>教师端</b><small>建设与管理知识库</small></button></div>
        <label>学号 / 工号<input v-model="account" autocomplete="username" placeholder="请输入学号或教师工号" @focus="activeField = 'account'" @blur="activeField = ''" /></label>
        <label>密码
          <span class="password-field">
            <input v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="请输入密码" @focus="activeField = 'password'" @blur="activeField = ''" />
        <button type="button" :aria-label="showPassword ? '隐藏密码' : '显示密码'" :title="showPassword ? '隐藏密码' : '显示密码'" @mousedown.prevent @click="showPassword = !showPassword"><SemiIcon :name="showPassword ? 'eye-closed' : 'eye-opened'" /></button>
          </span>
        </label>
        <div class="login-options"><label><input type="checkbox" /> 记住登录状态</label><a href="#">忘记密码？</a></div>
        <p v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</p>
        <button class="btn btn-primary login-submit" type="submit" :disabled="loading">{{ loading ? '正在验证…' : `登录${role === 'student' ? '学生端' : '教师后台'}` }}</button>
        <p class="prototype-tip">演示账号：学生 2023123456 / 教师 T20260001，密码 Campus@123</p>
      </form>
    </section>
  </main>
</template>
