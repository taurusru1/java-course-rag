<script setup>
import { onMounted, ref } from 'vue'
import { diagnose, getErrorCases } from '../api'

const error = ref('')
const loading = ref(false)
const result = ref(null)
const message = ref('')
const groups = ref([])

const sample = `Hello.java:5: error: cannot find symbol
        System.out.println(name);
                           ^
  symbol:   variable name
  location: class Hello`

async function run() {
  if (!error.value.trim()) {
    message.value = '请先粘贴报错信息'
    return
  }
  loading.value = true
  message.value = ''
  result.value = null
  try {
    const res = await diagnose(error.value)
    result.value = res.data
  } catch (e) {
    message.value = e.message
  } finally {
    loading.value = false
  }
}

function useSample() {
  error.value = sample
  result.value = null
  message.value = ''
}

onMounted(async () => {
  try {
    const res = await getErrorCases()
    groups.value = res.data || []
  } catch { /* 案例库加载失败不影响诊断 */ }
})
</script>

<template>
  <div>
    <header class="page-head">
      <h1>报错诊断</h1>
      <p>粘贴 javac 或运行时异常原文，系统按案例库匹配成因与修复步骤，并记录诊断轨迹用于准确率评估。</p>
    </header>

    <div class="grid two">
      <section class="card">
        <div class="toolbar" style="margin-bottom: 12px;">
          <h2 style="margin: 0;">① 粘贴报错</h2>
          <span class="spacer" />
          <button class="btn ghost small" type="button" @click="useSample">填入示例</button>
        </div>
        <textarea v-model="error" class="textarea" placeholder="例如：Hello.java:5: error: cannot find symbol …" />
        <div class="toolbar" style="margin-top: 14px;">
          <button class="btn" :disabled="loading" @click="run">{{ loading ? '诊断中…' : '开始诊断' }}</button>
          <span class="muted" style="font-size: 12.5px;">命中正则记 0.9，关键词记 0.7，低于 0.5 视为未命中</span>
        </div>
        <p v-if="message" class="error-text">{{ message }}</p>

        <div v-if="result" class="result" :class="result.matched ? 'ok' : ''" style="margin-top: 18px;">
          <h3>
            {{ result.matched ? `命中：${result.case.errorCode}` : '未命中已知案例' }}
            <span class="badge" :class="result.matched ? 'info' : ''">置信度 {{ result.confidence }}</span>
          </h3>
          <template v-if="result.matched">
            <p><span class="label">类别</span>{{ result.case.category }}</p>
            <p><span class="label">成因</span>{{ result.case.cause }}</p>
            <p><span class="label">修复建议</span>{{ result.case.solution }}</p>
            <pre v-if="result.case.exampleCode" class="code-block">{{ result.case.exampleCode }}</pre>
          </template>
          <p v-else>{{ result.suggestion }}</p>
        </div>
      </section>

      <section class="card">
        <h2>② 案例库</h2>
        <p class="muted" style="margin-bottom: 14px;">共 {{ groups.reduce((n, g) => n + g.cases.length, 0) }} 条，按类别分组。</p>
        <div v-if="!groups.length" class="empty">案例库为空</div>
        <div v-for="group in groups" :key="group.category" style="margin-bottom: 18px;">
          <div class="badge info" style="margin-bottom: 8px;">{{ group.category }}</div>
          <div v-for="item in group.cases" :key="item.id" class="chapter" style="padding: 10px 0;">
            <div class="chapter-no" style="font-size: 11px;">{{ item.id }}</div>
            <div>
              <b>{{ item.errorCode }}</b>
              <p>{{ item.cause }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
