<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthUser } from '../composables/useAuth'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close'])
const router = useRouter()
const inputRef = ref(null)
const query = ref('')
const activeIndex = ref(0)
const user = getAuthUser() || {}

const actions = computed(() => {
  const common = user.role === 'teacher'
    ? [
        { icon: 'dashboard', label: '打开数据概览', hint: '教师工作台', to: '/teacher/dashboard', keywords: 'dashboard 数据 统计' },
        { icon: 'upload', label: '上传知识资料', hint: '资料管理', to: '/teacher/knowledge', keywords: 'upload 上传 文档' },
        { icon: 'book', label: '管理课程分类', hint: '课程管理', to: '/teacher/courses', keywords: 'course 课程 分类' },
        { icon: 'chat', label: '预览学生问答', hint: '学生端', to: '/student/chat', query: { preview: 'teacher' }, keywords: 'chat 问答 预览' },
      ]
    : [
        { icon: 'dashboard', label: '返回学生首页', hint: '首页', to: '/student/home', keywords: 'home 首页' },
        { icon: 'chat', label: '开始智能问答', hint: '信息问答', to: '/student/chat', keywords: 'chat 提问 问答' },
        { icon: 'history', label: '查看问答记录', hint: '历史记录', to: '/student/history', keywords: 'history 历史 记录' },
        { icon: 'user', label: '查看个人资料', hint: '个人中心', to: '/student/profile', keywords: 'profile 个人 资料' },
      ]
  if (user.role === 'student' && query.value.trim()) {
    return [{ icon: 'send', label: `询问：“${query.value.trim()}”`, hint: '发送到智能问答', to: '/student/chat', ask: query.value.trim(), keywords: '' }, ...common]
  }
  return common
})
const filtered = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword || (user.role === 'student' && actions.value[0]?.ask)) return actions.value
  return actions.value.filter(item => `${item.label} ${item.hint} ${item.keywords}`.toLowerCase().includes(keyword))
})
const run = item => {
  if (!item) return
  router.push(item.ask ? { path: item.to, query: { q: item.ask } } : item.query ? { path: item.to, query: item.query } : item.to)
  emit('close')
}
const onKeydown = event => {
  if (!props.open) return
  if (event.key === 'Escape') emit('close')
  if (event.key === 'ArrowDown') { event.preventDefault(); activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1) }
  if (event.key === 'ArrowUp') { event.preventDefault(); activeIndex.value = Math.max(activeIndex.value - 1, 0) }
  if (event.key === 'Enter') { event.preventDefault(); run(filtered.value[activeIndex.value]) }
}
watch(() => props.open, value => {
  if (value) {
    query.value = ''
    activeIndex.value = 0
    nextTick(() => inputRef.value?.focus())
  }
})
watch(query, () => { activeIndex.value = 0 })
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="command-fade">
      <div v-if="open" class="command-backdrop" @mousedown.self="$emit('close')">
        <section class="command-panel" role="dialog" aria-modal="true" aria-label="快捷命令">
          <header><span><SemiIcon name="search" /></span><input ref="inputRef" v-model="query" :placeholder="user.role === 'student' ? '搜索页面，或直接输入问题…' : '搜索教师端功能…'" /><kbd>ESC</kbd></header>
          <div class="command-section-label">快捷操作</div>
          <div v-if="filtered.length" class="command-list">
            <button v-for="(item, index) in filtered" :key="`${item.to}-${item.label}`" :class="{ active: activeIndex === index }" @mouseenter="activeIndex = index" @click="run(item)">
              <span><SemiIcon :name="item.icon" /></span><div><b>{{ item.label }}</b><small>{{ item.hint }}</small></div><i>↵</i>
            </button>
          </div>
          <div v-else class="command-empty">没有匹配的功能</div>
          <footer><span><kbd>↑</kbd><kbd>↓</kbd> 选择</span><span><kbd>Enter</kbd> 打开</span><span>当前身份：{{ user.role === 'teacher' ? '教师' : '学生' }}</span></footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
