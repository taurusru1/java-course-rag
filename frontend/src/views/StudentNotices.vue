<script setup>
import { computed, onMounted, ref } from 'vue'
import { getPortalNotices } from '../api'
const active = ref('全部')
const notices = ref([
  { id: 1, title: '2025—2026 学年第二学期期末考试安排说明', dept: '教务处', category: '教学通知', date: '2026-06-18', important: true, content: '请各位同学及时登录教务系统查看个人考试安排，按要求携带有效证件参加考试。' },
  { id: 2, title: '暑期图书馆开放时间调整通知', dept: '图书馆', category: '校园服务', date: '2026-06-16', content: '暑假期间图书馆开放时间将进行调整，具体安排请查看图书馆通知。' },
  { id: 3, title: '国家助学金申请材料提交提醒', dept: '学生工作处', category: '学生事务', date: '2026-06-12', important: true, content: '符合条件的同学请在规定时间内完成申请材料提交。' },
  { id: 4, title: '校园网络系统维护通知', dept: '信息化中心', category: '校园服务', date: '2026-06-10', content: '维护期间部分校内系统可能出现短时无法访问的情况。' },
])
const categories = ['全部', '教学通知', '学生事务', '校园服务']
const filtered = computed(() => notices.value.filter(item => active.value === '全部' || item.category === active.value))
onMounted(async () => { try { notices.value = (await getPortalNotices()).data.data ?? notices.value } catch { /* 保留演示数据 */ } })
</script>

<template>
  <div class="student-page">
    <header class="student-page-heading"><div><h1>校园通知</h1><p>查看学校各部门发布的最新信息</p></div></header>
    <div class="record-tabs"><button v-for="item in categories" :key="item" :class="{ active: active === item }" @click="active = item">{{ item }}</button></div>
    <section class="notice-list">
      <article v-for="item in filtered" :key="item.id"><time><b>{{ (item.publishedAt || item.date).slice(8,10) }}</b><span>{{ (item.publishedAt || item.date).slice(0,7) }}</span></time><div><div><span>{{ item.category }}</span><em v-if="item.important">重要</em></div><h2>{{ item.title }}</h2><p>{{ item.content }}</p><small>发布部门：{{ item.department || item.dept }}</small></div><button>查看详情</button></article>
    </section>
  </div>
</template>
