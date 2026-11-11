<script setup>
import { computed, ref } from 'vue'
import SemiIcon from './SemiIcon.vue'

const storageKey = 'campus-kb-theme'
const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
const saved = window.localStorage.getItem(storageKey)
const theme = ref(saved === 'dark' || saved === 'light' ? saved : preferred)

const applyTheme = value => {
  document.documentElement.dataset.theme = value
  document.documentElement.style.colorScheme = value
}

applyTheme(theme.value)

const label = computed(() => theme.value === 'dark' ? '切换浅色模式' : '切换暗色模式')
const toggle = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  window.localStorage.setItem(storageKey, theme.value)
  applyTheme(theme.value)
}
</script>

<template>
  <button class="theme-toggle" type="button" :aria-label="label" :title="label" @click="toggle">
    <SemiIcon :name="theme === 'dark' ? 'sun' : 'moon'" />
    <small>{{ theme === 'dark' ? '浅色' : '暗色' }}</small>
  </button>
</template>
