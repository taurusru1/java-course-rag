<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getStudentHistory } from '../api'
const router = useRouter()
const search = ref('')
const active = ref('全部')
const records = ref([
  { id: 1, question: '国家奖学金的申请条件有哪些？', category: '学生事务', date: '今天 14:32', summary: '申请人须满足学业成绩、综合测评和在校表现等要求。' },
  { id: 2, question: '高等数学期末考试范围是什么？', category: '课程教学', date: '昨天 19:08', summary: '考试范围覆盖极限、导数、积分及其应用等章节。' },
  { id: 3, question: '学生证丢失后如何补办？', category: '办事指南', date: '06-16 10:25', summary: '可通过学生事务服务中心提交补办申请并缴纳工本费。' },
  { id: 4, question: '图书馆自习室周末几点开放？', category: '校园服务', date: '06-14 21:06', summary: '周末开放时间以图书馆最新通知为准。' },
])
const tabs = ['全部', '课程教学', '学生事务', '办事指南', '校园服务']
const filtered = computed(() => records.value.filter(item => (active.value === '全部' || item.category === active.value) && item.question.includes(search.value)))
onMounted(async () => { try { records.value = (await getStudentHistory()).data.data ?? records.value } catch { /* 保留演示数据 */ } })
</script>

<template>
  <div class="student-page">
    <header class="student-page-heading"><div><h1>问答记录</h1><p>查看和继续之前的信息查询</p></div><label>搜索记录<input v-model="search" placeholder="输入问题关键词" /></label></header>
    <div class="record-tabs"><button v-for="tab in tabs" :key="tab" :class="{ active: active === tab }" @click="active = tab">{{ tab }}</button></div>
    <section class="record-list">
    <article v-for="item in filtered" :key="item.id"><span class="record-mark"><SemiIcon name="chat" /></span><div><div class="record-meta"><span>{{ item.category }}</span><time>{{ item.date || item.createdAt?.replace('T', ' ').slice(0, 16) }}</time></div><h2>{{ item.question }}</h2><p>{{ item.summary || item.answer }}</p></div><button @click="router.push({ path: '/student/chat', query: { q: item.question } })">继续询问</button></article>
      <div v-if="!filtered.length" class="student-empty">没有找到匹配的问答记录。</div>
    </section>
  </div>
</template>
