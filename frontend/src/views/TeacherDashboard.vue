<script setup>
import { computed, onMounted, ref } from 'vue'
import { getTeacherDashboard } from '../api'

const data = ref(null)
const loading = ref(true)
const error = ref('')
const stats = computed(() => data.value ? [
  { label: '课程与分类', value: data.value.courseCount, note: '当前可维护范围', tone: 'blue' },
  { label: '知识资料', value: data.value.documentCount, note: `${data.value.doneCount} 份已完成`, tone: 'green' },
  { label: '解析任务', value: data.value.processingCount, note: `${data.value.failedCount} 份待处理`, tone: 'amber' },
  { label: '学生问答', value: data.value.questionCount, note: '已沉淀问答记录', tone: 'red' },
] : [])
const load = async () => {
  loading.value = true
  error.value = ''
  try { data.value = (await getTeacherDashboard()).data.data }
  catch (reason) { error.value = reason.response?.data?.message || '概览数据加载失败' }
  finally { loading.value = false }
}
const statusLabel = status => ({ done: '已入库', processing: '解析中', failed: '失败' }[status] || status)
const formatTime = value => value ? new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'
onMounted(load)
</script>

<template>
  <div class="dashboard teacher-dashboard">
    <div class="dashboard-heading">
      <div><span class="eyebrow">知识库运营台</span><h1>运行概览</h1><p>数据直接来自业务数据库，用于判断知识建设进度与待处理事项。</p></div>
      <div class="heading-actions"><button class="btn btn-secondary" @click="load"><SemiIcon name="refresh" />刷新数据</button><RouterLink class="btn btn-primary" to="/teacher/knowledge"><SemiIcon name="plus" />上传资料</RouterLink></div>
    </div>
    <p v-if="error" class="error-alert">{{ error }}</p>
    <div v-if="loading" class="state-card">正在汇总知识库数据…</div>
    <template v-else-if="data">
      <div class="stat-grid">
        <article v-for="item in stats" :key="item.label" :class="`stat-${item.tone}`"><span>{{ item.label }}</span><b>{{ item.value }}</b><small>{{ item.note }}</small></article>
      </div>
      <section v-if="data.failedCount" class="admin-attention"><span><SemiIcon name="warning" /></span><div><b>有 {{ data.failedCount }} 份资料解析失败</b><p>失败资料不会进入学生检索结果，建议前往资料管理检查并重新上传。</p></div><RouterLink to="/teacher/knowledge">立即处理 <SemiIcon name="arrow-right" /></RouterLink></section>
      <div class="dashboard-grid">
        <section class="panel">
          <div class="panel-heading"><div><h2>最近资料动态</h2><p>最新上传和解析状态</p></div><RouterLink to="/teacher/knowledge">管理资料</RouterLink></div>
          <div v-if="!data.recentDocuments.length" class="compact-empty">暂无资料动态</div>
          <div v-else class="activity-list">
            <article v-for="item in data.recentDocuments" :key="item.id">
              <span :class="['activity-icon', item.status]"><SemiIcon name="file" /></span>
              <div><b>{{ item.fileName }}</b><p>{{ item.courseName }} · {{ statusLabel(item.status) }}</p></div>
              <time>{{ formatTime(item.createdAt) }}</time>
            </article>
          </div>
        </section>
        <section class="panel">
          <div class="panel-heading"><div><h2>课程资料覆盖</h2><p>按资料数量排序</p></div><RouterLink to="/teacher/courses">管理课程</RouterLink></div>
          <div v-if="!data.courseUsage.length" class="compact-empty">暂无课程数据</div>
          <div v-else class="coverage-list">
            <div v-for="(item, index) in data.courseUsage" :key="item.id">
              <em>{{ String(index + 1).padStart(2, '0') }}</em><span><b>{{ item.name }}</b><small>{{ item.department }}</small></span><strong>{{ item.documentCount }}<small> 份</small></strong>
            </div>
          </div>
        </section>
      </div>
      <section class="teacher-shortcuts">
        <RouterLink to="/teacher/knowledge"><span><SemiIcon name="upload" /></span><div><b>导入资料</b><small>上传并追踪 AI 解析状态</small></div><i><SemiIcon name="arrow-right" /></i></RouterLink>
        <RouterLink to="/teacher/courses"><span><SemiIcon name="book" /></span><div><b>维护课程</b><small>新建、编辑和清理课程分类</small></div><i><SemiIcon name="arrow-right" /></i></RouterLink>
        <RouterLink :to="{ path: '/student/chat', query: { preview: 'teacher' } }"><span><SemiIcon name="chat" /></span><div><b>验证问答</b><small>切换到学生端检查检索效果</small></div><i><SemiIcon name="arrow-right" /></i></RouterLink>
      </section>
    </template>
  </div>
</template>
