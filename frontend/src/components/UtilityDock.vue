<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import CommandPalette from './CommandPalette.vue'
import HandDrawnClock from './HandDrawnClock.vue'
import { getAuthUser } from '../composables/useAuth'
import SemiIcon from './SemiIcon.vue'

const paletteOpen = ref(false)
const showTop = ref(false)
const user = getAuthUser() || {}
const updateScroll = () => { showTop.value = window.scrollY > 420 }
const globalShortcut = event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    paletteOpen.value = !paletteOpen.value
  }
}
onMounted(() => {
  window.addEventListener('scroll', updateScroll, { passive: true })
  window.addEventListener('keydown', globalShortcut)
  updateScroll()
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateScroll)
  window.removeEventListener('keydown', globalShortcut)
})
</script>

<template>
  <div class="utility-stack">
    <HandDrawnClock />
    <div class="utility-dock" aria-label="快捷工具">
      <button class="dock-command" title="快捷命令（Ctrl/⌘ + K）" aria-label="打开快捷命令" @click="paletteOpen = true"><SemiIcon name="command" /><small>快捷</small></button>
      <button v-if="showTop" title="回到顶部" aria-label="回到顶部" @click="window.scrollTo({ top: 0, behavior: 'smooth' })"><SemiIcon name="top" /><small>顶部</small></button>
      <div class="dock-role" :title="`当前账号：${user.account || ''}`"><SemiIcon name="user" /><i></i></div>
    </div>
  </div>
  <CommandPalette :open="paletteOpen" @close="paletteOpen = false" />
</template>
