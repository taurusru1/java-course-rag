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
const scope = ref('textbook')

const SAMPLES = [
  'Java 有哪些基本数据类型？',
  '类与对象是什么关系？',
  '多态是什么意思？',
]

const EXTENDED_SAMPLES = [
  'JVM 有哪些垃圾收集算法？',
  'AQS 的原理是什么？',
  'String 为什么是不可变的？',
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
    const start = await startChat(query, scope.value)
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

function initialScope() {
  const value = String(route.query.scope || '').trim()
  return ['textbook', 'extended', 'all'].includes(value) ? value : 'textbook'
}

onMounted(() => {
  scope.value = initialScope()
  scrollToBottom()
  const preset = String(route.query.q || '').trim()
  if (preset) ask(preset)
})
</script>

<template>
  <div>
    <div class="page-head">
      <h1>智能问答</h1>
      <p>默认在课程讲义里检索；讲义没讲到的问题，切到「含扩展资料」再问一次。</p>
    </div>

    <div class="card chat-card">
      <div ref="listRef" class="chat-list">
        <div v-if="!messages.length" class="chat-empty">
          <p>问点什么吧，比如：</p>
          <div class="tag-row">
            <button
              v-for="item in scope === 'extended' ? EXTENDED_SAMPLES : SAMPLES"
              :key="item"
              type="button"
              class="btn ghost small"
              @click="ask(item)"
            >
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
                  <span class="badge info">{{ source.tier === 'extended' ? '扩展阅读' : '课程讲义' }}</span>
                  <span class="source-path">{{ source.chapter_path || source.chapter_name || source.source_file }}</span>
                  <span class="source-file">{{ source.source_file }}</span>
                </div>
              </div>
            </template>
            <span v-else>{{ message.content }}</span>
          </div>
        </div>
      </div>

      <div class="scope-row">
        <span class="scope-label">检索范围</span>
        <button
          type="button"
          class="scope-chip"
          :class="{ active: scope === 'textbook' }"
          @click="scope = 'textbook'"
        >
          课程讲义
        </button>
        <button
          type="button"
          class="scope-chip"
          :class="{ active: scope === 'extended' }"
          @click="scope = 'extended'"
        >
          含扩展资料
        </button>
        <span class="scope-hint">{{ scope === 'extended' ? '在公开扩展资料（JavaGuide）中检索' : '只在本课程讲义中检索' }}</span>
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
