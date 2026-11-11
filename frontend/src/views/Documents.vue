<script setup>
import { computed, onMounted, ref } from 'vue'
import { deleteDocument, getCourses, listDocuments, uploadDocument } from '../api'

const courses = ref([])
const courseId = ref(null)
const documents = ref([])
const docType = ref('lecture')
const file = ref(null)
const uploading = ref(false)
const message = ref('')
const error = ref('')
const loading = ref(true)

const currentCourse = computed(() => courses.value.find(c => c.id === courseId.value))

const typeLabels = { lecture: '讲义', slides: '课件', code: '代码', exercise: '习题', other: '其他' }

function sizeText(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadDocuments() {
  if (!courseId.value) return
  try {
    const res = await listDocuments(courseId.value)
    documents.value = res.data || []
  } catch (e) {
    error.value = e.message
  }
}

async function pickCourse() {
  message.value = ''
  await loadDocuments()
}

function onFile(event) {
  file.value = event.target.files?.[0] || null
  message.value = ''
}

async function submit() {
  if (!file.value) {
    error.value = '请先选择要上传的资料文件'
    return
  }
  error.value = ''
  uploading.value = true
  message.value = ''
  try {
    const form = new FormData()
    form.append('file', file.value)
    form.append('courseId', String(courseId.value))
    form.append('docType', docType.value)
    const res = await uploadDocument(form)
    message.value = res.documentId
      ? `上传成功，已进入知识库（文档 #${res.documentId}）。现在去智能问答提问，就能检索到它。`
      : '上传完成'
    file.value = null
    await loadDocuments()
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
  }
}

async function remove(doc) {
  if (!window.confirm(`确定删除《${doc.fileName}》的记录吗？`)) return
  try {
    await deleteDocument(doc.id)
    await loadDocuments()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  try {
    const res = await getCourses()
    courses.value = res.data || []
    if (courses.value.length) {
      courseId.value = courses.value[0].id
      await loadDocuments()
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <header class="page-head">
      <h1>资料管理</h1>
      <p>上传讲义后会自动解析、切分并进入知识库，学生提问即可检索到新内容。</p>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="message" class="ok-text">{{ message }}</p>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!courses.length" class="empty">还没有课程，无法上传资料。</div>

    <div v-else class="grid two">
      <section class="card">
        <h2>上传新资料</h2>
        <p class="muted">支持 .md / .docx / .pdf。上传后由 Python 服务直接建索引，不依赖 Milvus。</p>

        <div class="field">
          <label>课程</label>
          <select v-model="courseId" @change="pickCourse">
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
        </div>

        <div class="field">
          <label>资料类型</label>
          <select v-model="docType">
            <option value="lecture">讲义</option>
            <option value="slides">课件</option>
            <option value="code">代码</option>
            <option value="exercise">习题</option>
            <option value="other">其他</option>
          </select>
        </div>

        <div class="field">
          <label>文件</label>
          <input type="file" accept=".md,.markdown,.docx,.pdf" @change="onFile" />
        </div>

        <div class="toolbar">
          <button type="button" class="btn" :disabled="uploading" @click="submit">
            {{ uploading ? '正在解析入库…' : '上传并入库' }}
          </button>
          <span class="spacer" />
          <span class="muted">{{ currentCourse ? currentCourse.name : '' }}</span>
        </div>
      </section>

      <section class="card">
        <div class="toolbar" style="margin-bottom: 8px;">
          <div>
            <h2>已上传资料</h2>
            <p class="muted">共 {{ documents.length }} 份</p>
          </div>
          <span class="spacer" />
          <button type="button" class="btn small ghost" @click="loadDocuments">刷新</button>
        </div>

        <div v-if="!documents.length" class="empty">这门课程还没有上传过资料</div>
        <div v-for="doc in documents" :key="doc.id" class="chapter">
          <div class="chapter-no">{{ (doc.fileName || '?').slice(0, 2).toUpperCase() }}</div>
          <div>
            <b>{{ doc.fileName }}</b>
            <p>
              {{ typeLabels[doc.docType] || doc.docType }} · {{ sizeText(doc.fileSize) }} ·
              <span class="badge" :class="doc.status === 'completed' ? 'ok' : doc.status === 'failed' ? 'bad' : ''">
                {{ doc.status === 'completed' ? '已入库' : doc.status === 'failed' ? '导入失败' : '处理中' }}
              </span>
            </p>
          </div>
          <button type="button" class="btn small ghost" @click="remove(doc)">删除</button>
        </div>
      </section>
    </div>
  </div>
</template>
