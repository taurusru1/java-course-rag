<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getCourses, getPracticeStats, getQuestions, getWrongAnswers, submitAnswer } from '../api'

const route = useRoute()
const courses = ref([])
const courseId = ref(null)
const questions = ref([])
const index = ref(0)
const selected = ref('')
const result = ref(null)
const loading = ref(true)
const error = ref('')
const stats = ref({ total: 0, wrong: 0, accuracy: 0 })
const wrongList = ref([])

const current = computed(() => questions.value[index.value] || null)
const options = computed(() => {
  const raw = current.value?.options
  if (!raw) return []
  try {
    const list = JSON.parse(raw)
    return list.map(text => {
      const match = String(text).match(/^([A-Za-z])[\s.、:：]+(.*)$/)
      return match ? { key: match[1].toUpperCase(), text: match[2] } : { key: '', text }
    })
  } catch {
    return []
  }
})
const needsText = computed(() => current.value && ['FILL', 'CODE'].includes(current.value.type))

function parseCourseId() {
  const id = Number(route.query.courseId)
  return Number.isFinite(id) && id > 0 ? id : null
}

async function loadQuestions(id) {
  loading.value = true
  error.value = ''
  try {
    const res = await getQuestions(id)
    questions.value = res.data || []
    index.value = 0
    selected.value = ''
    result.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function init() {
  try {
    const res = await getCourses()
    courses.value = res.data || []
    const wanted = parseCourseId() || courses.value[0]?.id
    if (wanted) {
      courseId.value = wanted
      await loadQuestions(wanted)
    }
  } catch (e) {
    error.value = e.message
    loading.value = false
  }
  await refreshStats()
}

async function refreshStats() {
  try {
    const [s, w] = await Promise.all([getPracticeStats(), getWrongAnswers()])
    stats.value = s.data || stats.value
    wrongList.value = w.data || []
  } catch { /* 统计失败不阻塞答题 */ }
}

async function choose(option) {
  if (result.value) return
  selected.value = option.key || option.text
}

async function submit() {
  if (!current.value || result.value) return
  if (!selected.value.trim()) {
    error.value = '请先作答'
    return
  }
  try {
    const res = await submitAnswer(current.value.id, selected.value)
    result.value = res.data
    await refreshStats()
  } catch (e) {
    error.value = e.message
  }
}

function next() {
  if (index.value < questions.value.length - 1) {
    index.value += 1
    selected.value = ''
    result.value = null
    error.value = ''
  }
}

async function switchCourse(id) {
  courseId.value = id
  await loadQuestions(id)
}

function optionClass(option) {
  if (!result.value) return { selected: selected.value === (option.key || option.text) }
  const key = option.key || option.text
  const standard = result.value.standardAnswer || ''
  return {
    right: String(standard).toUpperCase() === key.toUpperCase(),
    wrong: selected.value === key && String(standard).toUpperCase() !== key.toUpperCase(),
  }
}

onMounted(init)
</script>

<template>
  <div>
    <header class="page-head">
      <h1>练习与错题</h1>
      <p>客观题即时判分，答错自动进入错题本，并关联到知识点。</p>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>

    <div class="grid two">
      <section class="card">
        <div class="toolbar" style="margin-bottom: 16px;">
          <select class="select" style="width: auto;" :value="courseId" @change="switchCourse(Number($event.target.value))">
            <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
          </select>
          <span class="spacer" />
          <span class="badge info">{{ questions.length ? `${index + 1} / ${questions.length}` : '0 题' }}</span>
        </div>

        <div v-if="loading" class="empty">加载中…</div>
        <div v-else-if="!current" class="empty">该课程还没有题目</div>

        <template v-else>
          <div class="tag-row" style="margin-bottom: 10px;">
            <span class="badge">{{ current.type }}</span>
            <span v-if="current.difficulty" class="badge">难度 {{ current.difficulty }}</span>
            <span v-if="current.source" class="badge">{{ current.source }}</span>
          </div>

          <p class="q-stem">{{ current.stem }}</p>

          <div v-if="!needsText" class="options">
            <button
              v-for="option in options"
              :key="option.key + option.text"
              type="button"
              class="option"
              :class="optionClass(option)"
              @click="choose(option)"
            >
              <span class="key">{{ option.key || '·' }}</span>
              <span>{{ option.text }}</span>
            </button>
          </div>

          <input v-else v-model="selected" class="input" placeholder="输入你的答案" @keyup.enter="submit" />

          <div class="toolbar" style="margin-top: 18px;">
            <button class="btn" :disabled="!!result" @click="submit">提交答案</button>
            <button v-if="result" class="btn ghost" :disabled="index >= questions.length - 1" @click="next">下一题</button>
          </div>

          <div v-if="result" class="result" :class="result.correct ? 'ok' : 'bad'">
            <h3>{{ result.correct ? '回答正确' : '回答错误' }} · {{ result.score }} 分</h3>
            <p><span class="label">标准答案</span>{{ result.standardAnswer }}</p>
            <p v-if="result.analysis"><span class="label">解析</span>{{ result.analysis }}</p>
            <p v-if="result.knowledgePoint">
              <span class="label">知识点</span>
              {{ result.knowledgePoint.name }}（{{ result.knowledgePoint.code }}）
            </p>
          </div>
        </template>
      </section>

      <section class="card">
        <div class="stats" style="margin-bottom: 18px;">
          <div class="stat"><b>{{ stats.total }}</b><span>累计答题</span></div>
          <div class="stat"><b>{{ stats.wrong }}</b><span>错题</span></div>
          <div class="stat"><b>{{ Math.round((stats.accuracy || 0) * 100) }}%</b><span>正确率</span></div>
        </div>

        <h2>错题本</h2>
        <p class="muted" style="margin-bottom: 12px;">按时间倒序，点击题目可查看解析与知识点。</p>

        <div v-if="!wrongList.length" class="empty">还没有错题，继续保持。</div>
        <div v-for="item in wrongList" :key="item.recordId" class="chapter">
          <div class="chapter-no" style="background: var(--bad-soft); color: var(--bad);">!</div>
          <div>
            <b>{{ item.question?.stem }}</b>
            <p>
              你的答案：{{ item.userAnswer }}　标准答案：{{ item.question?.answer }}
            </p>
            <p v-if="item.knowledgePoint" class="muted">
              知识点：{{ item.knowledgePoint.name }}（{{ item.knowledgePoint.code }}）
            </p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
