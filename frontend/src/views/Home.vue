<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const question = ref('')
const quickQuestions = ['奖学金申请需要哪些材料？', '图书馆周末开放到几点？', '如何办理学生证补办？']
const services = [
  { icon: 'book', title: '课程与培养', text: '查询课程安排、培养方案与考试信息', color: 'blue' },
  { icon: 'file', title: '办事指南', text: '了解证明、证件和校园服务办理流程', color: 'green' },
  { icon: 'check', title: '规章制度', text: '快速检索学生手册和学校管理规定', color: 'orange' },
  { icon: 'home', title: '校园生活', text: '宿舍、食堂、图书馆等生活服务信息', color: 'purple' },
]
const notices = [
  { date: '06-18', title: '2025—2026 学年第二学期期末考试安排说明', tag: '教务' },
  { date: '06-16', title: '暑期图书馆开放时间调整通知', tag: '服务' },
  { date: '06-12', title: '国家助学金申请材料提交提醒', tag: '资助' },
]

const ask = (text = question.value) => {
  const value = text.trim()
  if (value) router.push({ path: '/chat', query: { q: value } })
}
</script>

<template>
  <div>
    <section class="hero">
      <div class="hero-copy">
        <span class="eyebrow">基于校内可信资料的 AI 助手</span>
        <h1>校园问题，<em>现在就问。</em></h1>
        <p>课程安排、办事流程、规章制度与校园生活信息，一次提问即可获得带来源的答案。</p>
        <form class="hero-search" @submit.prevent="ask()">
          <SemiIcon name="search" />
          <input v-model="question" aria-label="输入校园问题" placeholder="例如：转专业申请需要满足哪些条件？" />
          <button class="btn btn-primary" type="submit" :disabled="!question.trim()">立即提问</button>
        </form>
        <div class="quick-row">
          <span>大家都在问：</span>
          <button v-for="item in quickQuestions" :key="item" type="button" @click="ask(item)">{{ item }}</button>
        </div>
      </div>
      <div class="hero-visual" aria-hidden="true">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <div class="ai-core"><span>AI</span><small>校园知识中枢</small></div>
        <div class="float-card card-a"><SemiIcon name="check" /> 引用校内资料</div>
        <div class="float-card card-b">24h 随时可问</div>
        <div class="float-card card-c">1,286 份资料</div>
      </div>
    </section>

    <section class="section">
      <div class="section-heading"><div><span class="eyebrow">常用服务</span><h2>你想了解什么？</h2></div><RouterLink to="/courses">查看全部 <SemiIcon name="arrow-right" /></RouterLink></div>
      <div class="service-grid">
        <article v-for="item in services" :key="item.title" class="service-card">
          <span :class="['service-icon', item.color]"><SemiIcon :name="item.icon" /></span>
          <h3>{{ item.title }}</h3><p>{{ item.text }}</p>
          <RouterLink :to="{ path: '/chat', query: { q: `请介绍${item.title}相关信息` } }">开始查询 <SemiIcon name="arrow-right" /></RouterLink>
        </article>
      </div>
    </section>

    <section class="section split-section">
      <div class="notice-panel">
        <div class="section-heading"><div><span class="eyebrow">最新动态</span><h2>校园通知</h2></div></div>
        <article v-for="notice in notices" :key="notice.title" class="notice-item">
          <time>{{ notice.date }}</time><div><span class="tag">{{ notice.tag }}</span><h3>{{ notice.title }}</h3></div><SemiIcon name="arrow-right" />
        </article>
      </div>
      <div class="feature-panel">
        <span class="eyebrow light">为什么选择校园智答</span><h2>答案有依据，查询更放心</h2>
        <ul><li><b>01</b><span><strong>来源可追溯</strong>每条回答展示参考资料和章节</span></li><li><b>02</b><span><strong>校内知识专属</strong>围绕学校资料提供针对性答案</span></li><li><b>03</b><span><strong>持续更新</strong>教师上传资料后即可进入知识库</span></li></ul>
      </div>
    </section>
  </div>
</template>
