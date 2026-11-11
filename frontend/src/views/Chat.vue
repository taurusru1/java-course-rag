<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getChatStatus, startChat } from '../api'

const route = useRoute()

const messages = ref([])
const question = ref('')
const sending = ref(false)
const error = ref('')
const listRef = ref(null)

const SAMPLES = [
  'Java 有哪些基本数据类型？',
  '类与对象是什么关系？',
  '数组的长度可以改变吗？',
]

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

async function ask(text) {
  const query = (text ?? question.value).trim()
  if (!query || sending.value) return
  error.value = ''
  question.value = ''
  messages.value.push({ role: 'user', content: query })
  messages.value.push({ role: 'assistant', content: '', sources: [], status: 'running' })
  const current = messages.value[messages.value.length - 1]
  sending.value = true
  scrollToBottom()

  try {
    const start = await startChat(query)
    const sessionId = start.sessionId
    for (let i = 0; i < 120; i += 1) {
      await new Promise(resolve => setTimeout(resolve, 500))
      const res = await getChatStatus(sessionId)
      if (res.status === 'completed' || res.answer) {
        current.content = res.answer || ''
        current.sources = res.sources || []
        current.status = 'done'
        break
      }
    }
    if (current.status !== 'done') {
      current.content = '回答超时，请确认 AI 服务是否已启动（默认 127.0.0.1:9000）。'
      current.status = 'error'
    }
  } catch (e) {
    current.content = `调用失败：${e.message}`
    current.status = 'error'
    error.value = e.message
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  scrollToBottom()
  const preset = String(route.query.q || '').trim()
  if (preset) ask(preset)
})
</script>

<template>
  <div>
    <div class="page-head">
      <h1>智能问答</h1>
      <p>基于课程讲义检索作答，回答下方会标注引用的章节与来源文件。</p>
    </div>

    <div class="card chat-card">
      <div ref="listRef" class="chat-list">
        <div v-if="!messages.length" class="chat-empty">
          <p>问点什么吧，比如：</p>
          <div class="tag-row">
            <button v-for="item in SAMPLES" :key="item" type="button" class="btn ghost small" @click="ask(item)">
              {{ item }}
            </button>
          </div>
        </div>

        <div v-for="(message, i) in messages" :key="i" class="bubble-row" :class="message.role">
          <div class="bubble" :class="message.role">
            <template v-if="message.role === 'assistant'">
              <span v-if="message.status === 'running'" class="typing">正在检索课程知识库…</span>
              <span v-else class="answer-text">{{ message.content }}</span>
              <div v-if="message.sources?.length" class="sources">
                <div class="sources-title">引用来源</div>
                <div v-for="source in message.sources" :key="source.chunk_id" class="source-item">
                  <span class="badge info">{{ source.source === 'knowledge_base' ? '知识库' : '联网' }}</span>
                  <span class="source-path">{{ source.chapter_path || source.chapter_name || source.source_file }}</span>
                  <span class="source-file">{{ source.source_file }}</span>
                </div>
              </div>
            </template>
            <span v-else>{{ message.content }}</span>
          </div>
        </div>
      </div>

      <form class="chat-input" @submit.prevent="ask()">
        <input
          v-model="question"
          class="input"
          placeholder="输入你的 Java 问题，回车发送"
          :disabled="sending"
        />
        <button class="btn" type="submit" :disabled="sending || !question.trim()">
          {{ sending ? '回答中…' : '发送' }}
        </button>
      </form>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>
