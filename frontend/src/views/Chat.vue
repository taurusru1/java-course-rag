<script setup>
import MarkdownIt from 'markdown-it'
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  chatStreamUrl,
  deleteChatSession,
  getChatMessages,
  getChatResult,
  getChatSessions,
  startChat,
  submitFeedback,
} from '../api'
import RiveMotion from '../components/RiveMotion.vue'
import IconAIFilledLevel2 from '../components/IconAIFilledLevel2.vue'

const route = useRoute()
const markdown = new MarkdownIt({ breaks: true, html: false, linkify: true })
const defaultLinkOpen = markdown.renderer.rules.link_open
markdown.renderer.rules.link_open = (tokens, index, options, env, self) => {
  tokens[index].attrSet('target', '_blank')
  tokens[index].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen ? defaultLinkOpen(tokens, index, options, env, self) : self.renderToken(tokens, index, options)
}

const query = ref('')
const messages = ref([])
const busy = ref(false)
const listRef = ref(null)
const textareaRef = ref(null)
const sidebarOpen = ref(false)
const sessions = ref([])
const sessionsLoading = ref(false)
const sessionsError = ref('')
const activeSessionId = ref('')
const showScrollButton = ref(false)
let activeStream = null

const sampleQuestions = ['本学期补考如何申请？', '奖学金评定标准是什么？', '图书馆借阅逾期如何处理？']
const createId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
const createMessage = (role, text = '', extra = {}) => ({
  id: createId(),
  role,
  text,
  timestamp: Date.now(),
  sources: [],
  thinking: false,
  streaming: false,
  error: false,
  feedback: '',
  ...extra,
})

const renderMarkdown = text => markdown.render(text || '')
const formatMessageTime = value => {
  const date = new Date(value || Date.now())
  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()
  const time = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  return sameDay ? time : `${date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })} ${time}`
}
const formatSessionTime = value => {
  if (!value) return ''
  return new Date(value * 1000).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
const isNearBottom = () => {
  const el = listRef.value
  return !el || el.scrollHeight - el.scrollTop - el.clientHeight <= 200
}
const scrollToBottom = (force = false) => nextTick(() => {
  const el = listRef.value
  if (!el) return
  if (force || isNearBottom()) {
    el.scrollTo({ top: el.scrollHeight, behavior: force ? 'smooth' : 'auto' })
    showScrollButton.value = false
  } else if (busy.value) {
    showScrollButton.value = true
  }
})
const handleScroll = () => {
  showScrollButton.value = busy.value && !isNearBottom()
}
const resizeTextarea = event => {
  const el = event?.target || textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  el.style.overflowY = el.scrollHeight > 120 ? 'auto' : 'hidden'
}
const resetTextarea = () => nextTick(() => {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.overflowY = 'hidden'
})

const loadSessions = async () => {
  sessionsLoading.value = true
  sessionsError.value = ''
  try {
    sessions.value = (await getChatSessions()).data.data || []
    if (!activeSessionId.value && sessions.value.length) activeSessionId.value = sessions.value[0].sessionId
  } catch (error) {
    console.error('加载会话列表失败', error)
    sessions.value = []
    sessionsError.value = '会话记录暂时无法加载'
  } finally {
    sessionsLoading.value = false
  }
}
const newChat = () => {
  stopGeneration()
  activeSessionId.value = ''
  messages.value = []
  query.value = ''
  sidebarOpen.value = false
  resetTextarea()
}
const openSession = async session => {
  stopGeneration()
  activeSessionId.value = session.sessionId
  messages.value = []
  try {
    const { data } = await getChatMessages(session.sessionId)
    messages.value = (data.data || []).map(item => createMessage(item.role, item.text, {
      id: item.id || createId(),
      timestamp: item.timestamp ? item.timestamp * 1000 : Date.now(),
      sources: item.sources || [],
      feedback: readFeedback(session.sessionId, item.id),
    }))
    sidebarOpen.value = false
    scrollToBottom(true)
  } catch (error) {
    console.error('加载会话消息失败', error)
  }
}
const removeSession = async (session, event) => {
  event.stopPropagation()
  if (!window.confirm(`删除对话“${session.title}”？`)) return
  try {
    await deleteChatSession(session.sessionId)
    if (activeSessionId.value === session.sessionId) newChat()
    await loadSessions()
  } catch (error) {
    console.error('删除会话失败', error)
  }
}

const stopGeneration = () => {
  activeStream?.close()
  activeStream = null
  const current = [...messages.value].reverse().find(item => item.role === 'assistant' && (item.streaming || item.thinking))
  if (current) {
    current.streaming = false
    current.thinking = false
    current.stopped = true
    if (!current.text) current.text = '已停止生成。'
  }
  busy.value = false
  showScrollButton.value = false
}
const userFacingError = error => {
  if (!navigator.onLine || error?.code === 'ERR_NETWORK') return '网络连接失败，请检查网络后重试'
  if (error?.response?.status >= 500) return '服务繁忙，请稍后重试'
  return '服务响应异常，请重试'
}
const recoverChatResult = async (sessionId, aiMsg) => {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const { data } = await getChatResult(sessionId)
    if (data.status === 'done') {
      aiMsg.thinking = false
      aiMsg.streaming = false
      aiMsg.text = data.answer || '暂未检索到可用答案。'
      aiMsg.sources = (data.sources || []).map(source => ({ ...source, expanded: false }))
      busy.value = false
      showScrollButton.value = false
      await loadSessions()
      scrollToBottom()
      return
    }
    if (data.status === 'failed') throw new Error(data.error || 'query failed')
    await new Promise(resolve => setTimeout(resolve, 2000))
  }
  throw new Error('query timed out')
}
const sendQuick = text => send(text)
const send = async (overrideText, options = {}) => {
  const text = String(overrideText ?? query.value).trim()
  if (!text || busy.value) return
  const userMsg = options.appendUser === false ? null : createMessage('user', text)
  const aiMsg = reactive(createMessage('assistant', '', { thinking: true, streaming: true }))
  if (userMsg) messages.value.push(userMsg)
  messages.value.push(aiMsg)
  query.value = ''
  busy.value = true
  resetTextarea()
  scrollToBottom(true)

  try {
    const { data } = await startChat(text, null)
    const sessionId = data.sessionId || data.taskId || data.data?.sessionId
    if (!sessionId) throw Object.assign(new Error('missing session id'), { userMessage: '服务响应异常，请重试' })
    activeSessionId.value = sessionId
    activeStream = new EventSource(chatStreamUrl(sessionId))
    const recoveryPromise = recoverChatResult(sessionId, aiMsg).catch(recoveryError => {
      if (!busy.value) return
      console.error('查询结果恢复失败', recoveryError)
      aiMsg.thinking = false
      aiMsg.streaming = false
      aiMsg.error = true
      aiMsg.text ||= '查询超时，请重试'
      busy.value = false
      showScrollButton.value = false
      activeStream?.close()
      activeStream = null
    })
    activeStream.addEventListener('answer_chunk', event => {
      const shouldAutoScroll = isNearBottom()
      aiMsg.thinking = false
      aiMsg.streaming = true
      aiMsg.text += JSON.parse(event.data).content || ''
      scrollToBottom(shouldAutoScroll)
    })
    activeStream.addEventListener('final', event => {
      const result = JSON.parse(event.data)
      aiMsg.thinking = false
      aiMsg.streaming = false
      aiMsg.text ||= result.answer || '暂未检索到可用答案。'
      aiMsg.sources = (result.sources || []).map(source => ({ ...source, expanded: false }))
      busy.value = false
      showScrollButton.value = false
      activeStream?.close()
      activeStream = null
      loadSessions()
      scrollToBottom()
    })
    activeStream.onerror = error => {
      console.error('SSE 连接中断', error)
      activeStream?.close()
      activeStream = null
      void recoveryPromise
    }
  } catch (error) {
    console.error('发送消息失败', error)
    aiMsg.thinking = false
    aiMsg.streaming = false
    aiMsg.error = true
    aiMsg.text = error.userMessage || userFacingError(error)
    busy.value = false
  }
}
const retryMessage = index => {
  const errorMessage = messages.value[index]
  let userIndex = index - 1
  while (userIndex >= 0 && messages.value[userIndex].role !== 'user') userIndex -= 1
  if (userIndex < 0) return
  const text = messages.value[userIndex].text
  messages.value.splice(index, 1)
  send(text, { appendUser: false })
}
const copy = async msg => {
  await navigator.clipboard?.writeText(msg.text)
  msg.copied = true
  setTimeout(() => { msg.copied = false }, 1200)
}
const feedbackKey = (sessionId, messageId) => `chat_feedback:${sessionId || 'new'}:${messageId || ''}`
const readFeedback = (sessionId, messageId) => localStorage.getItem(feedbackKey(sessionId, messageId)) || ''
const setFeedback = async (msg, index, type) => {
  msg.feedback = type
  localStorage.setItem(feedbackKey(activeSessionId.value, msg.id), msg.feedback)
  try {
    await submitFeedback(activeSessionId.value, index, msg.feedback)
  } catch (error) {
    console.error('反馈接口暂不可用，已保存到本地', error)
  }
}
const toggleSource = source => {
  if (source.excerpt) source.expanded = !source.expanded
}

onMounted(async () => {
  await loadSessions()
  if (route.query.q) send(String(route.query.q))
})
onBeforeUnmount(stopGeneration)
</script>

<template>
  <div class="chat-page">
    <aside class="chat-sidebar" :class="{ open: sidebarOpen }">
      <button class="new-chat" type="button" @click="newChat"><SemiIcon name="plus" /> 新建对话</button>
      <p class="side-label">最近对话</p>
      <div v-if="sessionsLoading" class="session-list-state" role="status">正在加载会话记录…</div>
      <div v-else-if="sessionsError" class="session-list-state is-error" role="alert">
        <span>{{ sessionsError }}</span>
        <button type="button" @click="loadSessions">重新加载</button>
      </div>
      <div v-else-if="!sessions.length" class="session-list-state">暂无会话，发起提问后会保存在这里</div>
      <button v-for="item in sessions" :key="item.sessionId" :class="['session-item', { active: activeSessionId === item.sessionId }]" type="button" @click="openSession(item)">
        <span class="session-ai-icon"><IconAIFilledLevel2 /></span>
        <span><b>{{ item.title }}</b><em>{{ item.lastMessage || '新对话' }}</em><small>{{ formatSessionTime(item.updatedAt) }}</small></span>
        <i class="session-delete" role="button" aria-label="删除对话" title="删除对话" @click="removeSession(item, $event)"><SemiIcon name="delete" /></i>
      </button>
      <div class="sidebar-note"><b>知识库状态</b><span><i></i> 校内资料可查询</span></div>
    </aside>

    <section class="chat-workspace">
      <header class="chat-toolbar">
        <button class="sidebar-trigger" type="button" aria-label="打开会话列表" @click="sidebarOpen = !sidebarOpen"><SemiIcon name="menu" /></button>
        <div><h1>智能问答</h1><p>答案来自校内知识库，并提供资料来源</p></div>
      </header>

      <div ref="listRef" class="message-list" aria-live="polite" @scroll="handleScroll">
        <div v-if="!messages.length" class="chat-empty">
          <RiveMotion class="chat-empty-rive" src="https://cdn.rive.app/animations/skills.riv" label="等待提问动画" />
          <h2>请问你要查询什么？</h2>
          <p>可查询办事流程、规章制度和校园生活信息，回答将标明资料来源。</p>
          <div class="prompt-grid"><button v-for="item in sampleQuestions" :key="item" @click="sendQuick(item)">{{ item }}<SemiIcon name="arrow-right" /></button></div>
        </div>

        <TransitionGroup name="message-rise">
          <article v-for="(msg, index) in messages" :key="msg.id" :class="['message', msg.role]">
            <div class="avatar"><SemiIcon v-if="msg.role === 'user'" name="user" /><IconAIFilledLevel2 v-else /></div>
            <div class="message-content">
              <div :class="['bubble', { error: msg.error }]">
                <div v-if="msg.thinking" class="typing"><RiveMotion class="typing-rive" src="https://cdn.rive.app/animations/vehicles.riv" /><em>正在检索校内资料</em></div>
                <p v-else-if="msg.role === 'user'">{{ msg.text }}</p>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.text)"></div>
                <span v-if="msg.streaming && !msg.thinking" class="stream-cursor" aria-label="正在生成">|</span>
                <small v-if="msg.stopped" class="stopped-label">已停止生成</small>
                <time>{{ formatMessageTime(msg.timestamp) }}</time>
              </div>
              <button v-if="msg.error" class="retry-button" type="button" @click="retryMessage(index)"><SemiIcon name="refresh" /> 重试</button>
              <div v-if="msg.sources?.length" class="sources">
                <b>参考来源</b>
                <component
                  :is="source.url ? 'a' : 'button'"
                  v-for="(source, sourceIndex) in msg.sources"
                  :key="source.chunk_id || sourceIndex"
                  class="source-card"
                  :href="source.url || undefined"
                  :target="source.url ? '_blank' : undefined"
                  rel="noopener noreferrer"
                  type="button"
                  @click="!source.url && toggleSource(source)"
                >
                  <span><SemiIcon :name="source.url ? 'globe' : 'file'" /></span>
                  <div><strong>{{ source.doc_title || source.title }}</strong><small>{{ source.chapter || '校内知识库' }}</small><p v-if="source.expanded">{{ source.excerpt }}</p></div>
                </component>
              </div>
              <div v-if="msg.role === 'assistant' && !msg.thinking" class="message-actions">
                <button @click="copy(msg)"><SemiIcon name="copy" />{{ msg.copied ? '已复制' : '复制' }}</button>
                <button :class="{ active: msg.feedback === 'up' }" @click="setFeedback(msg, index, 'up')"><SemiIcon name="like" />有帮助</button>
                <button :class="{ active: msg.feedback === 'down' }" @click="setFeedback(msg, index, 'down')"><SemiIcon name="dislike" />需改进</button>
              </div>
            </div>
          </article>
        </TransitionGroup>

        <Transition name="scroll-fade">
          <button v-if="showScrollButton" class="scroll-bottom-button" type="button" aria-label="回到底部" @click="scrollToBottom(true)"><SemiIcon name="arrow-down" /></button>
        </Transition>
      </div>

      <form class="composer" @submit.prevent="busy ? stopGeneration() : send()">
        <textarea ref="textareaRef" v-model="query" :disabled="busy" rows="1" placeholder="输入你的问题，Enter 发送，Shift+Enter 换行" @input="resizeTextarea" @keydown.enter.exact.prevent="send()" />
        <button type="submit" :disabled="!busy && !query.trim()" :aria-label="busy ? '停止生成' : '发送'"><SemiIcon :name="busy ? 'stop' : 'send'" /></button>
        <small>AI 回答可能存在偏差，重要信息请核对参考来源。</small>
      </form>
    </section>

    <aside class="chat-context">
      <span class="eyebrow">使用提示</span><h3>这样提问更准确</h3>
      <ol><li>说明你的年级或专业</li><li>写清楚想办理的具体事项</li><li>补充时间、地点等关键信息</li></ol>
      <div class="context-card"><b>找不到答案？</b><p>可以换一种描述，或联系对应业务部门确认。</p></div>
    </aside>
  </div>
</template>
