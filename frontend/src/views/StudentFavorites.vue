<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getStudentFavorites, removeStudentFavorite } from '../api'
const router = useRouter()
const favorites = ref([
  { id: 1, title: '国家奖学金申请条件与材料清单', type: '问答', source: '学生工作处 · 奖助学金管理办法', date: '收藏于 06-18' },
  { id: 2, title: '学生证补办流程', type: '办事指南', source: '学生事务服务中心', date: '收藏于 06-16' },
  { id: 3, title: '图书馆借阅与续借规则', type: '规章制度', source: '图书馆读者服务规定', date: '收藏于 06-12' },
])
const remove = async id => { try { await removeStudentFavorite(1, id) } catch { /* 本地仍可移除 */ } favorites.value = favorites.value.filter(item => item.id !== id) }
onMounted(async () => { try { favorites.value = (await getStudentFavorites()).data.data ?? favorites.value } catch { /* 保留演示数据 */ } })
</script>

<template>
  <div class="student-page">
    <header class="student-page-heading"><div><h1>我的收藏</h1><p>保存重要答案和常用校内信息</p></div><span class="record-count">{{ favorites.length }} 项内容</span></header>
    <section class="favorite-grid">
      <article v-for="item in favorites" :key="item.id"><div class="favorite-type">{{ item.itemType || item.type }}</div><h2>{{ item.title }}</h2><p>{{ item.source }}</p><footer><span>{{ item.date || '已收藏' }}</span><div><button @click="router.push({ path: '/student/chat', query: { q: item.title } })">查看</button><button @click="remove(item.id)">取消收藏</button></div></footer></article>
      <div v-if="!favorites.length" class="student-empty">暂无收藏内容，可在查看回答时添加收藏。</div>
    </section>
  </div>
</template>
