<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getStudentProfile, updateStudentProfile } from '../api'
const editing = ref(false)
const saved = ref(false)
const form = reactive({ name: '林同学', studentNo: '2023123456', college: '信息工程学院', major: '计算机科学与技术', grade: '2023级', email: 'lin@example.edu.cn' })
const save = async () => { await updateStudentProfile(1, { name: form.name, email: form.email }); editing.value = false; saved.value = true; setTimeout(() => saved.value = false, 1800) }
onMounted(async () => { try { Object.assign(form, (await getStudentProfile()).data.data) } catch { /* 保留演示数据 */ } })
</script>

<template>
  <div class="student-page">
    <header class="student-page-heading"><div><h1>个人中心</h1><p>查看个人信息与平台使用设置</p></div></header>
    <div class="profile-layout">
  <aside class="profile-summary"><span><SemiIcon name="user" /></span><h2>{{ form.name }}</h2><p>{{ form.studentNo }}</p><dl><div><dt>本学期提问</dt><dd>18</dd></div><div><dt>收藏内容</dt><dd>6</dd></div></dl></aside>
      <section class="profile-form">
    <header><div><h2>基本信息</h2><p>信息来源于校内统一身份系统</p></div><button v-if="!editing" @click="editing = true"><SemiIcon name="edit" />编辑信息</button></header>
        <div class="profile-fields"><label>姓名<input v-model="form.name" :disabled="!editing" /></label><label>学号<input v-model="form.studentNo" disabled /></label><label>学院<input v-model="form.college" disabled /></label><label>专业<input v-model="form.major" disabled /></label><label>年级<input v-model="form.grade" disabled /></label><label>联系邮箱<input v-model="form.email" :disabled="!editing" /></label></div>
        <footer v-if="editing"><button @click="editing = false">取消</button><button class="primary" @click="save">保存修改</button></footer>
        <p v-if="saved" class="profile-success">个人信息已保存</p>
      </section>
    </div>
  </div>
</template>
