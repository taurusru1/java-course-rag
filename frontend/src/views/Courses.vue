<script setup>
import { computed, onMounted, ref } from 'vue'
import { createCourse, deleteCourse, getCourses, updateCourse } from '../api'

const courses = ref([])
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const search = ref('')
const showForm = ref(false)
const editingId = ref(null)
const form = ref({ name: '', code: '', department: '', semester: '', description: '' })
const filtered = computed(() => courses.value.filter(item =>
  [item.name, item.code, item.department, item.semester].some(value => String(value || '').toLowerCase().includes(search.value.toLowerCase()))
))
const load = async () => {
  loading.value = true; error.value = ''
  try { courses.value = (await getCourses()).data.data || [] }
  catch (reason) { error.value = reason.response?.data?.message || '课程加载失败' }
  finally { loading.value = false }
}
const openCreate = () => {
  editingId.value = null
  form.value = { name: '', code: '', department: '', semester: '2025-2026-2', description: '' }
  showForm.value = true
}
const openEdit = item => {
  editingId.value = item.id
  form.value = { name: item.name || '', code: item.code || '', department: item.department || '', semester: item.semester || '', description: item.description || '' }
  showForm.value = true
}
const save = async () => {
  error.value = ''; success.value = ''
  if (!form.value.name.trim()) { error.value = '课程名称不能为空'; return }
  saving.value = true
  try {
    if (editingId.value) await updateCourse(editingId.value, form.value)
    else await createCourse(form.value)
    success.value = editingId.value ? '课程信息已更新' : '课程已创建'
    showForm.value = false
    await load()
  } catch (reason) { error.value = reason.response?.data?.message || '保存失败，请检查课程编号是否重复' }
  finally { saving.value = false }
}
const remove = async item => {
  if (!window.confirm(`确认删除“${item.name}”？课程下存在资料时将无法删除。`)) return
  error.value = ''; success.value = ''
  try { await deleteCourse(item.id); success.value = '课程已删除'; await load() }
  catch (reason) { error.value = reason.response?.data?.message || '删除失败，请先清理该课程下的资料' }
}
onMounted(load)
</script>

<template>
  <div class="teacher-management">
  <div class="dashboard-heading"><div><span class="eyebrow">知识结构</span><h1>课程与分类管理</h1><p>维护资料归属，确保学生检索时能够定位到正确知识范围。</p></div><button class="btn btn-primary" @click="openCreate"><SemiIcon name="plus" /> 新建课程</button></div>
  <div class="management-toolbar"><label><SemiIcon name="search" /><input v-model="search" placeholder="搜索课程名称、编号、院系或学期" /></label><span>共 {{ courses.length }} 个课程</span></div>
    <p v-if="error" class="error-alert">{{ error }}</p><p v-if="success" class="success-alert">{{ success }}</p>
    <div v-if="loading" class="state-card">正在加载课程…</div>
    <div v-else-if="!filtered.length" class="state-card"><b>没有匹配课程</b><p>调整搜索词或新建课程。</p></div>
    <section v-else class="panel management-table">
      <div class="table-wrap"><table><thead><tr><th>课程信息</th><th>编号</th><th>所属院系</th><th>学期</th><th>操作</th></tr></thead>
        <tbody><tr v-for="item in filtered" :key="item.id">
          <td><div class="course-name-cell"><span>{{ item.name.slice(0, 1) }}</span><div><strong>{{ item.name }}</strong><small>{{ item.description || '暂未填写课程说明' }}</small></div></div></td>
          <td><code>{{ item.code || '—' }}</code></td><td>{{ item.department || '未设置' }}</td><td>{{ item.semester || '未设置' }}</td>
          <td><div class="row-actions"><button @click="openEdit(item)">编辑</button><button class="danger" @click="remove(item)">删除</button></div></td>
        </tr></tbody></table></div>
    </section>
    <div v-if="showForm" class="admin-modal" @click.self="showForm = false">
      <form class="admin-modal-card" @submit.prevent="save">
      <div class="modal-heading"><div><span class="eyebrow">{{ editingId ? '编辑课程' : '创建课程' }}</span><h2>{{ editingId ? '更新课程信息' : '添加新的知识范围' }}</h2></div><button type="button" aria-label="关闭" @click="showForm = false"><SemiIcon name="close" /></button></div>
        <div class="form-grid"><label>课程名称 *<input v-model="form.name" placeholder="例如：数据库原理" /></label><label>课程编号<input v-model="form.code" placeholder="例如：CS305" /></label><label>所属院系<input v-model="form.department" placeholder="例如：信息工程学院" /></label><label>开课学期<input v-model="form.semester" placeholder="例如：2025-2026-2" /></label></div>
        <label class="wide-field">课程说明<textarea v-model="form.description" rows="4" placeholder="说明课程内容和资料覆盖范围"></textarea></label>
        <div class="modal-actions"><button type="button" class="btn btn-secondary" @click="showForm = false">取消</button><button class="btn btn-primary" :disabled="saving">{{ saving ? '保存中…' : '保存课程' }}</button></div>
      </form>
    </div>
  </div>
</template>
