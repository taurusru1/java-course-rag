<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api'
import { setAuthSession } from '../composables/useAuth'

const router = useRouter()
const role = ref('STUDENT')
const account = ref('student')
const password = ref('123456')
const loading = ref(false)
const error = ref('')

function switchRole(next) {
  role.value = next
  account.value = next === 'TEACHER' ? 'teacher' : 'student'
  password.value = '123456'
  error.value = ''
}

async function submit() {
  if (!account.value.trim() || !password.value) {
    error.value = '请输入账号和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await login(account.value.trim(), password.value, role.value)
    setAuthSession(res.data.token, res.data.user)
    router.push('/courses')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-art">
      <div>
        <h1>基于 RAG 的<br />Java 程序课程辅导系统</h1>
        <p>
          课程知识检索、代码感知切分、编译报错诊断与错题溯源，
          把「查文档」变成「问到点上」。
        </p>
        <div class="tags">
          <span>混合检索 + 重排</span>
          <span>代码感知切分</span>
          <span>javac 报错定位</span>
          <span>错题溯源</span>
        </div>
      </div>
      <p style="font-size: 12.5px; color: #7f90ad;">毕业设计 · 三端架构 Spring Boot + Vue + Python</p>
    </section>

    <section class="login-form-wrap">
      <form class="login-form" @submit.prevent="submit">
        <h2>登录</h2>
        <p class="sub">使用课程账号进入学习空间</p>

        <div class="role-tabs">
          <button type="button" :class="{ active: role === 'STUDENT' }" @click="switchRole('STUDENT')">学生</button>
          <button type="button" :class="{ active: role === 'TEACHER' }" @click="switchRole('TEACHER')">教师</button>
        </div>

        <div class="field">
          <label>账号</label>
          <input v-model="account" class="input" autocomplete="username" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" class="input" autocomplete="current-password" />
        </div>

        <button class="btn" style="width: 100%;" :disabled="loading">
          {{ loading ? '登录中…' : '进入系统' }}
        </button>
        <p v-if="error" class="error-text">{{ error }}</p>

        <p class="hint">
          演示账号：学生 student / 123456，教师 teacher / 123456<br />
          首次启动由 DataSeeder 自动创建。
        </p>
      </form>
    </section>
  </div>
</template>
