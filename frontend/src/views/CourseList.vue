<script setup>
import { onMounted, ref } from 'vue'
import { getChapters, getCourses } from '../api'

const courses = ref([])
const chapters = ref([])
const selected = ref(null)
const loading = ref(true)
const error = ref('')

async function pick(course) {
  selected.value = course
  chapters.value = []
  try {
    const res = await getChapters(course.id)
    chapters.value = res.data || []
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  try {
    const res = await getCourses()
    courses.value = res.data || []
    if (courses.value.length) await pick(courses.value[0])
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
      <h1>课程与章节</h1>
      <p>课程 → 章节 → 知识点三级导航，右侧可直接进入对应练习。</p>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <div v-if="loading" class="empty">加载中…</div>

    <div v-else-if="!courses.length" class="empty">还没有课程数据，请先运行后端 DataSeeder 或导入课程。</div>

    <div v-else class="grid two">
      <section>
        <div class="grid cards">
          <article
            v-for="course in courses"
            :key="course.id"
            class="card course-card"
            :class="{ active: selected?.id === course.id }"
            @click="pick(course)"
          >
            <span class="course-code">{{ course.code || 'COURSE' }}</span>
            <h2>{{ course.name }}</h2>
            <p class="course-desc">{{ course.description || '暂无课程简介' }}</p>
            <div class="tag-row">
              <span v-if="course.semester" class="badge">{{ course.semester }}</span>
              <span v-if="course.department" class="badge">{{ course.department }}</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="selected" class="card">
        <div class="toolbar" style="margin-bottom: 8px;">
          <div>
            <h2>{{ selected.name }}</h2>
            <p class="muted">共 {{ chapters.length }} 个章节</p>
          </div>
          <span class="spacer" />
          <RouterLink class="btn small" :to="{ path: '/practice', query: { courseId: selected.id } }">去练习</RouterLink>
        </div>

        <div v-if="!chapters.length" class="empty">该课程还没有章节</div>
        <div v-for="chapter in chapters" :key="chapter.id" class="chapter">
          <div class="chapter-no">{{ chapter.chapterNo }}</div>
          <div>
            <b>{{ chapter.title }}</b>
            <p>{{ chapter.summary }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
