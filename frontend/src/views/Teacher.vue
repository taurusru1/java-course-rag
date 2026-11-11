<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  createChapter,
  createQuestion,
  deleteChapter,
  getChapters,
  getCourses,
  getKnowledgePoints,
  getTeacherStats,
} from '../api'

const courses = ref([])
const courseId = ref(null)
const chapters = ref([])
const points = ref([])
const stats = ref(null)
const tab = ref(initialTab())
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const message = ref('')

function initialTab() {
  const value = new URLSearchParams(window.location.search).get('tab')
  return ['chapter', 'question', 'stats'].includes(value) ? value : 'chapter'
}

const chapterForm = ref({ title: '', summary: '' })
const questionForm = ref({
  chapterId: '',
  knowledgePointId: '',
  type: 'CHOICE',
  stem: '',
  options: '',
  answer: '',
  analysis: '',
  difficulty: 2,
})

const typeLabels = { CHOICE: '单选', MULTI: '多选', JUDGE: '判断', FILL: '填空', CODE: '编程' }
const needOptions = computed(() => ['CHOICE', 'MULTI', 'JUDGE'].includes(questionForm.value.type))

async function reload() {
  if (!courseId.value) return
  try {
    const [chapterRes, pointRes] = await Promise.all([
      getChapters(courseId.value),
      getKnowledgePoints(courseId.value),
    ])
    chapters.value = chapterRes.data || []
    points.value = pointRes.data || []
    if (tab.value === 'stats') await loadStats()
  } catch (e) {
    error.value = e.message
  }
}

async function loadStats() {
  if (!courseId.value) return
  try {
    const res = await getTeacherStats(courseId.value)
    stats.value = res.data
  } catch (e) {
    error.value = e.message
  }
}

async function pickCourse() {
  error.value = ''
  message.value = ''
  stats.value = null
  questionForm.value.chapterId = ''
  questionForm.value.knowledgePointId = ''
  await reload()
}

async function switchTab(name) {
  tab.value = name
  error.value = ''
  if (name === 'stats') await loadStats()
}

async function addChapter() {
  if (!chapterForm.value.title.trim()) {
    error.value = '章节标题不能为空'
    return
  }
  error.value = ''
  busy.value = true
  try {
    const res = await createChapter(courseId.value, {
      title: chapterForm.value.title.trim(),
      summary: chapterForm.value.summary.trim(),
    })
    message.value = `已新增第 ${res.data.chapterNo} 章`
    chapterForm.value = { title: '', summary: '' }
    await reload()
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function removeChapter(chapter) {
  if (!window.confirm(`删除《${chapter.title}》？该章节下的题目不会自动删除。`)) return
  try {
    await deleteChapter(chapter.id)
    message.value = '章节已删除'
    await reload()
  } catch (e) {
    error.value = e.message
  }
}

function parseOptions(text) {
  const lines = text.split('\n').map(s => s.trim()).filter(Boolean)
  return JSON.stringify(lines.map((line, i) => (/^[A-Z][.、]/.test(line) ? line : `${String.fromCharCode(65 + i)}. ${line}`)))
}

async function addQuestion() {
  const f = questionForm.value
  if (!f.stem.trim()) {
    error.value = '题干不能为空'
    return
  }
  if (!f.answer.trim()) {
    error.value = '请填写标准答案'
    return
  }
  error.value = ''
  busy.value = true
  try {
    await createQuestion({
      courseId: courseId.value,
      chapterId: f.chapterId || null,
      knowledgePointId: f.knowledgePointId || null,
      type: f.type,
      stem: f.stem.trim(),
      optionsJson: needOptions.value ? parseOptions(f.options) : null,
      answer: f.answer.trim(),
      analysis: f.analysis.trim(),
      difficulty: Number(f.difficulty) || 2,
      source: '教师录入',
    })
    message.value = '题目已加入题库，学生端刷新即可看到'
    questionForm.value = { ...questionForm.value, stem: '', options: '', answer: '', analysis: '' }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function pct(value) {
  return `${Math.round((value || 0) * 1000) / 10}%`
}

onMounted(async () => {
  try {
    const res = await getCourses()
    courses.value = res.data || []
    if (courses.value.length) {
      courseId.value = courses.value[0].id
      await reload()
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <header class="page-head">
      <h1>教师中心</h1>
      <p>维护章节与题库，并查看本课程的学情。所有改动立即对学生端生效。</p>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="message" class="ok-text">{{ message }}</p>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!courses.length" class="empty">还没有课程。</div>

    <template v-else>
      <div class="toolbar" style="margin-bottom: 14px;">
        <div class="field" style="margin: 0; min-width: 220px;">
          <label>课程</label>
          <select v-model="courseId" @change="pickCourse">
            <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
          </select>
        </div>
        <span class="spacer" />
        <span class="muted">{{ chapters.length }} 章 · {{ points.length }} 个知识点</span>
      </div>

      <div class="tabs">
        <button type="button" :class="{ active: tab === 'chapter' }" @click="switchTab('chapter')">章节管理</button>
        <button type="button" :class="{ active: tab === 'question' }" @click="switchTab('question')">录入题目</button>
        <button type="button" :class="{ active: tab === 'stats' }" @click="switchTab('stats')">学情统计</button>
      </div>

      <div v-if="tab === 'chapter'" class="grid two">
        <section class="card">
          <h2>新增章节</h2>
          <p class="muted">章节号自动取当前最大值 +1。</p>
          <div class="field">
            <label>章节标题</label>
            <input v-model="chapterForm.title" placeholder="例如：异常处理与 IO" />
          </div>
          <div class="field">
            <label>章节简介</label>
            <textarea v-model="chapterForm.summary" rows="3" placeholder="一句话说明本章讲什么" />
          </div>
          <button type="button" class="btn" :disabled="busy" @click="addChapter">
            {{ busy ? '提交中…' : '新增章节' }}
          </button>
        </section>

        <section class="card">
          <h2>现有章节</h2>
          <div v-if="!chapters.length" class="empty">还没有章节</div>
          <div v-for="chapter in chapters" :key="chapter.id" class="chapter">
            <div class="chapter-no">{{ chapter.chapterNo }}</div>
            <div>
              <b>{{ chapter.title }}</b>
              <p>{{ chapter.summary || '暂无简介' }}</p>
            </div>
            <button type="button" class="btn small ghost" @click="removeChapter(chapter)">删除</button>
          </div>
        </section>
      </div>

      <div v-else-if="tab === 'question'" class="grid two">
        <section class="card">
          <h2>录入题目</h2>
          <div class="field">
            <label>章节</label>
            <select v-model="questionForm.chapterId">
              <option value="">不指定</option>
              <option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
                第 {{ chapter.chapterNo }} 章 {{ chapter.title }}
              </option>
            </select>
          </div>
          <div class="field">
            <label>知识点</label>
            <select v-model="questionForm.knowledgePointId">
              <option value="">不指定</option>
              <option v-for="point in points" :key="point.id" :value="point.id">{{ point.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>题型</label>
            <select v-model="questionForm.type">
              <option value="CHOICE">单选</option>
              <option value="MULTI">多选</option>
              <option value="JUDGE">判断</option>
              <option value="FILL">填空</option>
              <option value="CODE">编程</option>
            </select>
          </div>
          <div class="field">
            <label>题干</label>
            <textarea v-model="questionForm.stem" rows="3" placeholder="题目描述" />
          </div>
          <div v-if="needOptions" class="field">
            <label>选项（每行一个，会自动补 A. / B. 前缀）</label>
            <textarea v-model="questionForm.options" rows="4" placeholder="2name&#10;_name&#10;class&#10;my-name" />
          </div>
          <div class="field">
            <label>标准答案</label>
            <input v-model="questionForm.answer" placeholder="如 B；多选写 AC；判断题写 T；填空题写关键字；编程题写期望输出" />
          </div>
          <div class="field">
            <label>解析</label>
            <textarea v-model="questionForm.analysis" rows="2" placeholder="为什么是这个答案" />
          </div>
          <button type="button" class="btn" :disabled="busy" @click="addQuestion">
            {{ busy ? '提交中…' : '加入题库' }}
          </button>
        </section>

        <section class="card">
          <h2>录入说明</h2>
          <ul class="muted" style="line-height: 1.9; padding-left: 18px;">
            <li>单选题答案写选项字母，多选按字母顺序写，如 <code>AC</code>。</li>
            <li>判断题答案写 <code>T</code> / <code>F</code>，选项可留空（系统按「正确 / 错误」判）。</li>
            <li>填空题答案会忽略大小写与首尾空白。</li>
            <li>编程题的答案栏填<b>期望输出</b>，判分时真实编译运行学生代码并逐行比对。</li>
            <li>题目加入后，学生端「练习与错题」会立即出现。</li>
          </ul>
          <p class="muted">题型：{{ Object.entries(typeLabels).map(([k, v]) => `${k}=${v}`).join('，') }}</p>
        </section>
      </div>

      <div v-else>
        <div v-if="!stats" class="empty">加载中…</div>
        <template v-else>
          <div class="stat-grid">
            <div class="card stat"><span>答题人次</span><b>{{ stats.summary.answered }}</b></div>
            <div class="card stat"><span>错题人次</span><b>{{ stats.summary.wrong }}</b></div>
            <div class="card stat"><span>平均正确率</span><b>{{ pct(stats.summary.accuracy) }}</b></div>
            <div class="card stat"><span>参与学生</span><b>{{ stats.summary.students }}</b></div>
            <div class="card stat"><span>题目数</span><b>{{ stats.summary.questions }}</b></div>
            <div class="card stat"><span>已覆盖题目</span><b>{{ stats.summary.coveredQuestions }}</b></div>
          </div>

          <div class="grid two" style="margin-top: 14px;">
            <section class="card">
              <h2>知识点掌握情况</h2>
              <div v-if="!stats.byKnowledgePoint.length" class="empty">还没有答题记录</div>
              <table v-else class="table">
                <thead><tr><th>知识点</th><th>作答</th><th>错</th><th>正确率</th></tr></thead>
                <tbody>
                  <tr v-for="row in stats.byKnowledgePoint" :key="row.label">
                    <td>{{ row.label }}</td><td>{{ row.answered }}</td><td>{{ row.wrong }}</td><td>{{ pct(row.accuracy) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="card">
              <h2>最难的五道题</h2>
              <div v-if="!stats.hardestQuestions.length" class="empty">还没有答题记录</div>
              <table v-else class="table">
                <thead><tr><th>题目</th><th>作答</th><th>正确率</th></tr></thead>
                <tbody>
                  <tr v-for="row in stats.hardestQuestions" :key="row.questionId">
                    <td class="ellipsis">{{ row.label }}</td><td>{{ row.answered }}</td><td>{{ pct(row.accuracy) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </div>

          <section class="card" style="margin-top: 14px;">
            <h2>学生答题概况</h2>
            <div v-if="!stats.byStudent.length" class="empty">还没有答题记录</div>
            <table v-else class="table">
              <thead><tr><th>学生</th><th>作答</th><th>错</th><th>正确率</th></tr></thead>
              <tbody>
                <tr v-for="row in stats.byStudent" :key="row.userId">
                  <td>{{ row.name }}</td><td>{{ row.answered }}</td><td>{{ row.wrong }}</td><td>{{ pct(row.accuracy) }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </template>
      </div>
    </template>
  </div>
</template>
