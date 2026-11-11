<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { deleteDocument, getCourses, getDocument, getDocuments, uploadDocument } from '../api'
import { computed } from 'vue'

const courses = ref([])
const courseId = ref('')
const docType = ref('lecture')
const file = ref(null)
const documents = ref([])
const loadingDocs = ref(false)
const uploading = ref(false)
const progress = ref(0)
const status = ref('')
const error = ref('')
const dragOver = ref(false)
const demoMode = ref(false)
const statusFilter = ref('all')
const keyword = ref('')
let pollTimer

const demoDocuments = [
  { id: 'd1', name: '2025版学生手册.pdf', course: '学生事务指南', type: '规章制度', status: 'done', updatedAt: '2026-06-18 14:30' },
  { id: 'd2', name: '高等数学课程大纲.pdf', course: '高等数学', type: '教学大纲', status: 'processing', updatedAt: '2026-06-18 13:05' },
  { id: 'd3', name: '奖助学金办理说明.docx', course: '学生事务指南', type: '办事指南', status: 'failed', updatedAt: '2026-06-17 16:20' },
]
const normalizeDocuments = list => list.map(item => ({
  ...item,
  name: item.name || item.fileName || item.title || '未命名资料',
  course: item.courseName || item.course || '未分类',
  type: item.docType || item.type || '资料',
  updatedAt: item.updatedAt || item.createdAt || '—',
}))
const filteredDocuments = computed(() => documents.value.filter(item =>
  (statusFilter.value === 'all' || item.status === statusFilter.value)
  && [item.name, item.course, item.type].some(value => String(value || '').toLowerCase().includes(keyword.value.toLowerCase()))
))
const loadDocuments = async () => {
  loadingDocs.value = true
  try { documents.value = normalizeDocuments((await getDocuments(courseId.value || undefined)).data.data ?? []) }
  catch { documents.value = demoDocuments; demoMode.value = true }
  finally { loadingDocs.value = false }
}
onMounted(async () => {
  try { courses.value = (await getCourses()).data.data ?? [] }
  catch { error.value = '课程服务暂未连接，上传功能需要后端服务。'; demoMode.value = true }
  loadDocuments()
})
onBeforeUnmount(() => clearInterval(pollTimer))

const selectFile = selected => {
  error.value = ''
  if (!selected) return
  if (!/\.(pdf|md|docx?)$/i.test(selected.name)) { error.value = '仅支持 PDF、Markdown 和 Word 文档。'; return }
  file.value = selected
}
const onDrop = event => { event.preventDefault(); dragOver.value = false; selectFile(event.dataTransfer.files[0]) }
const submit = async () => {
  error.value = ''; status.value = ''
  if (!courseId.value) { error.value = '请选择资料所属课程。'; return }
  if (!file.value) { error.value = '请选择需要上传的文件。'; return }
  uploading.value = true; progress.value = 0
  try {
    const data = new FormData()
    data.append('file', file.value); data.append('courseId', courseId.value); data.append('docType', docType.value)
    const response = await uploadDocument(data, event => { if (event.total) progress.value = Math.round(event.loaded * 100 / event.total) })
    const documentId = response.data.documentId || response.data.data?.id
    if (!documentId) throw new Error('接口未返回资料编号')
    status.value = '上传完成，AI 正在解析资料。'
    poll(documentId)
  } catch (reason) {
    error.value = reason.response?.data?.message || '上传失败，请确认 Java 后端和 AI 服务已启动。'
    uploading.value = false
  }
}
const poll = id => {
  clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const response = await getDocument(id)
      const data = response.data.data ?? response.data
      if (data.status === 'done') { status.value = '资料解析完成，已进入知识库。'; uploading.value = false; clearInterval(pollTimer); loadDocuments() }
      if (data.status === 'failed') { error.value = data.error || '资料解析失败。'; status.value = ''; uploading.value = false; clearInterval(pollTimer); loadDocuments() }
    } catch { /* 短暂轮询失败不生成伪成功状态 */ }
  }, 2000)
}
const formatSize = size => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : ''
const removeDocument = async doc => {
  if (!window.confirm(`确认删除“${doc.name}”？此操作不会自动删除已经生成的向量索引。`)) return
  try { await deleteDocument(doc.id); status.value = '资料记录已删除。'; await loadDocuments() }
  catch (reason) { error.value = reason.response?.data?.message || '删除资料失败。' }
}
</script>

<template>
  <div class="page-container">
    <section class="page-banner admin-banner"><span class="eyebrow">教师与管理员</span><h1>知识资料管理</h1><p>上传校内可信资料，AI 将自动解析并建立检索索引。</p></section>
    <p v-if="demoMode" class="demo-alert">演示模式：资料列表为示例数据，只有连接后端后才能真实上传。</p>
    <div class="admin-layout">
      <section class="panel upload-panel">
        <div class="panel-heading"><div><span class="step">1</span><div><h2>上传新资料</h2><p>支持 PDF、Markdown、Word</p></div></div></div>
        <div class="form-grid"><label>所属课程<select v-model="courseId"><option value="">请选择课程</option><option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option></select></label>
          <label>资料类型<select v-model="docType"><option value="lecture">课程课件</option><option value="textbook">教材资料</option><option value="exam">考试资料</option><option value="syllabus">教学大纲</option><option value="other">其他资料</option></select></label></div>
        <div class="drop-zone" :class="{ active: dragOver, ready: file }" @dragover.prevent="dragOver = true" @dragleave="dragOver = false" @drop="onDrop">
          <input id="document-file" type="file" accept=".pdf,.md,.doc,.docx" @change="selectFile($event.target.files[0])" />
          <label for="document-file"><span><SemiIcon :name="file ? 'check' : 'upload'" /></span><strong>{{ file ? file.name : '拖放文件到这里，或点击选择' }}</strong><small>{{ file ? formatSize(file.size) : '单个文件建议不超过 50MB' }}</small></label>
        </div>
        <div v-if="uploading" class="progress-wrap"><div><span :style="{ width: `${progress}%` }"></span></div><small>{{ status || `上传中 ${progress}%` }}</small></div>
        <p v-if="status && !uploading" class="success-alert">{{ status }}</p><p v-if="error" class="error-alert">{{ error }}</p>
        <button class="btn btn-primary full-btn" :disabled="uploading" @click="submit">{{ uploading ? '处理中…' : '上传并开始解析' }}</button>
      </section>

      <aside class="panel process-panel"><span class="eyebrow">处理流程</span><h2>资料如何进入知识库</h2><ol><li><b>01</b><span><strong>上传校内资料</strong>选择课程和资料类型</span></li><li><b>02</b><span><strong>AI 自动解析</strong>提取文本并切分知识片段</span></li><li><b>03</b><span><strong>建立检索索引</strong>学生提问时提供来源依据</span></li></ol></aside>
    </div>

    <section class="panel document-panel">
      <div class="panel-heading"><div><h2>资料列表</h2><p>筛选、检查和清理知识资料</p></div><button class="btn btn-secondary" @click="loadDocuments">刷新</button></div>
      <div class="document-toolbar"><label><SemiIcon name="search" /><input v-model="keyword" placeholder="搜索文件或课程" /></label><select v-model="statusFilter"><option value="all">全部状态</option><option value="done">已完成</option><option value="processing">解析中</option><option value="failed">失败</option></select><span>{{ filteredDocuments.length }} / {{ documents.length }} 份</span></div>
      <div v-if="loadingDocs" class="state-card">正在加载资料…</div>
      <div v-else-if="!filteredDocuments.length" class="state-card"><b>没有匹配资料</b><p>调整关键词或状态筛选。</p></div>
      <div v-else class="table-wrap"><table><thead><tr><th>文件</th><th>所属课程</th><th>类型</th><th>状态</th><th>更新时间</th><th>操作</th></tr></thead>
        <tbody><tr v-for="doc in filteredDocuments" :key="doc.id"><td><strong>{{ doc.name }}</strong></td><td>{{ doc.course }}</td><td>{{ doc.type }}</td><td><span :class="['status-pill', doc.status]">{{ doc.status === 'done' ? '已完成' : doc.status === 'failed' ? '失败' : '解析中' }}</span></td><td>{{ doc.updatedAt }}</td><td><button class="table-delete" @click="removeDocument(doc)">删除</button></td></tr></tbody></table></div>
    </section>
  </div>
</template>
