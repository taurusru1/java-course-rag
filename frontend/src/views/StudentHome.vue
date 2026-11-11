<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPortalNotices, getStudentHistory, getStudentSummary } from '../api'
import { getAuthUser } from '../composables/useAuth'
import RiveMotion from '../components/RiveMotion.vue'
import IconAIFilledLevel2 from '../components/IconAIFilledLevel2.vue'

const router = useRouter()
const route = useRoute()
const user = getAuthUser() || {}
const studentId = user.studentId || 1
const question = ref('')
const loading = ref(true)
const notices = ref([])
const history = ref([])
const summary = ref({ historyCount: 0, favoriteCount: 0, categoryCount: 0 })
const selectedNotice = ref(null)

const services = [
  { icon: 'user', title: '学生证补办', text: '查看挂失、申请与领取流程', question: '学生证丢失后如何挂失和补办？' },
  { icon: 'favorite', title: '奖助学金', text: '申请条件、材料与时间安排', question: '奖助学金申请需要哪些条件和材料？' },
  { icon: 'file', title: '校园卡服务', text: '挂失、充值和故障处理', question: '校园卡丢失后如何挂失和补办？' },
  { icon: 'book', title: '图书馆服务', text: '开放时间、借阅与数据库', question: '图书馆开放时间和借阅规则是什么？' },
  { icon: 'globe', title: '校园网络', text: '网络认证、邮箱和系统帮助', question: '校园网如何连接，认证失败怎么办？' },
  { icon: 'chat', title: '心理咨询', text: '预约方式与紧急求助渠道', question: '学校心理咨询如何预约？' },
  { icon: 'history', title: '考试安排', text: '考试时间、地点和证件要求', question: '如何查询本学期考试安排和考场？' },
  { icon: 'check', title: '证明开具', text: '在读证明、成绩单办理', question: '在读证明和成绩单如何申请？' },
]
const tasks = computed(() => [
  { day: '25', month: '06月', title: '第一轮选课开放', meta: '教务系统 · 09:00 开始', status: '即将开始', tone: 'blue' },
  { day: '30', month: '06月', title: '奖助学金材料截止', meta: '学生工作处 · 17:00 截止', status: '剩余 7 天', tone: 'red' },
  { day: '05', month: '07月', title: '期末考试周开始', meta: '请提前查询个人考试安排', status: '本学期', tone: 'amber' },
])
const importantNotices = computed(() => notices.value.filter(item => item.important).slice(0, 3))
const recentHistory = computed(() => history.value.slice(0, 3))
const previewQuery = computed(() => route.query.preview === 'teacher' ? { preview: 'teacher' } : {})

const go = path => router.push({ path, query: previewQuery.value })
const ask = text => {
  const value = String(text ?? question.value).trim()
  if (value) router.push({ path: '/student/chat', query: { ...previewQuery.value, q: value } })
}
const formatDate = value => value ? new Date(value).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) : '—'

onMounted(async () => {
  const results = await Promise.allSettled([
    getPortalNotices(),
    getStudentHistory(studentId),
    getStudentSummary(studentId),
  ])
  if (results[0].status === 'fulfilled') notices.value = results[0].value.data.data || []
  if (results[1].status === 'fulfilled') history.value = results[1].value.data.data || []
  if (results[2].status === 'fulfilled') summary.value = results[2].value.data.data || summary.value
  loading.value = false
})
</script>

<template>
  <div class="student-page student-home">
    <section class="student-welcome">
      <div class="welcome-heading">
        <div><p>你好，{{ user.displayName || '同学' }}</p><h1>今天想查询什么信息？</h1><span>平台内容来源于校内知识库，回答将标明参考依据。</span></div>
        <RiveMotion class="welcome-rive" src="https://cdn.rive.app/animations/skills.riv" label="校园知识助手动画" />
      </div>
      <form @submit.prevent="ask()"><input v-model="question" placeholder="输入课程、办事流程或校园生活问题" /><button>开始查询</button></form>
      <div class="quick-questions"><span>常用查询</span><button @click="ask('奖学金申请需要哪些材料？')">奖学金申请</button><button @click="ask('学生证丢失如何补办？')">学生证补办</button><button @click="ask('图书馆周末开放时间？')">图书馆时间</button></div>
    </section>

    <section class="student-section">
    <header class="student-section-title"><div><h2>校园服务</h2><p>常用事项直接查询，减少查找入口的时间</p></div><button class="section-text-button" @click="ask('请列出常用校园服务和办理入口')">查看全部服务 <SemiIcon name="arrow-right" /></button></header>
      <div class="student-service-grid">
      <button v-for="item in services" :key="item.title" @click="ask(item.question)"><b><SemiIcon :name="item.icon" /></b><span><strong>{{ item.title }}</strong><small>{{ item.text }}</small></span><i><SemiIcon name="arrow-right" /></i></button>
      </div>
    </section>

    <section class="student-section student-home-columns">
      <div class="student-panel">
        <header class="student-section-title"><div><h2>近期事项</h2><p>本学期需要关注的时间节点</p></div></header>
        <div class="student-timeline">
          <article v-for="item in tasks" :key="item.title">
            <time><b>{{ item.day }}</b><span>{{ item.month }}</span></time>
            <i></i>
            <div><span :class="`task-${item.tone}`">{{ item.status }}</span><h3>{{ item.title }}</h3><p>{{ item.meta }}</p></div>
          </article>
        </div>
      </div>
      <div class="student-panel student-summary-panel">
        <header class="student-section-title"><div><h2>我的使用概览</h2><p>知识服务使用记录</p></div></header>
        <div v-if="loading" class="home-loading">正在加载…</div>
        <div v-else class="usage-summary">
          <button @click="go('/student/history')"><b>{{ summary.historyCount }}</b><span>问答记录</span></button>
          <button @click="go('/student/favorites')"><b>{{ summary.favoriteCount }}</b><span>收藏内容</span></button>
          <button @click="go('/student/notices')"><b>{{ importantNotices.length }}</b><span>重要通知</span></button>
        </div>
    <div class="student-summary-note"><span><IconAIFilledLevel2 /></span><p>需要办理具体业务时，请在答案中核对发布部门和更新时间。</p></div>
      </div>
    </section>

    <section class="student-section student-home-columns lower">
      <div class="student-panel">
    <header class="student-section-title"><div><h2>重要通知</h2><p>来自校内部门的近期提醒</p></div><button class="section-text-button" @click="go('/student/notices')">查看全部 <SemiIcon name="arrow-right" /></button></header>
        <div v-if="loading" class="home-loading">正在加载通知…</div>
        <div v-else-if="importantNotices.length" class="student-home-notices">
          <button v-for="item in importantNotices" :key="item.id" @click="selectedNotice = item">
      <time>{{ formatDate(item.publishedAt) }}</time><span><b>{{ item.title }}</b><small>{{ item.department }} · {{ item.category }}</small></span><i><SemiIcon name="arrow-right" /></i>
          </button>
        </div>
        <div v-else class="home-empty">暂无重要通知</div>
      </div>
      <div class="student-panel">
    <header class="student-section-title"><div><h2>最近问答</h2><p>继续上次的信息查询</p></div><button class="section-text-button" @click="go('/student/history')">查看记录 <SemiIcon name="arrow-right" /></button></header>
        <div v-if="loading" class="home-loading">正在加载记录…</div>
        <div v-else-if="recentHistory.length" class="student-recent-list">
      <button v-for="item in recentHistory" :key="item.id" @click="ask(item.question)"><span><SemiIcon name="chat" /></span><div><b>{{ item.question }}</b><small>{{ item.category || '校园信息' }} · {{ formatDate(item.createdAt) }}</small></div><i>继续 <SemiIcon name="arrow-right" /></i></button>
        </div>
        <div v-else class="home-empty">暂无问答记录，试着提出第一个问题。</div>
      </div>
    </section>

    <Teleport to="body">
      <div v-if="selectedNotice" class="notice-drawer-backdrop" @click.self="selectedNotice = null">
        <aside class="notice-drawer">
    <header><div><span>{{ selectedNotice.category }}</span><h2>{{ selectedNotice.title }}</h2></div><button aria-label="关闭" @click="selectedNotice = null"><SemiIcon name="close" /></button></header>
          <p>{{ selectedNotice.content }}</p>
          <footer><span>发布部门：{{ selectedNotice.department }}</span><time>{{ formatDate(selectedNotice.publishedAt) }}</time></footer>
        </aside>
      </div>
    </Teleport>
  </div>
</template>
