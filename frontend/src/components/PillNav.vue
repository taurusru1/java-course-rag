<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  items: { type: Array, required: true },
  teacherPreview: { type: Boolean, default: false },
})

const route = useRoute()
const mobileOpen = ref(false)
const destination = path => props.teacherPreview ? { path, query: { preview: 'teacher' } } : path
</script>

<template>
  <div class="campus-pill-nav">
    <nav class="campus-pill-items" aria-label="主要导航">
      <RouterLink
        v-for="(item, index) in items"
        :key="item.to"
        :to="destination(item.to)"
        :class="['campus-pill', { active: route.path === item.to }]"
      >
        <span class="campus-pill-index" aria-hidden="true">0{{ index + 1 }}</span>
        <span class="campus-pill-label">{{ item.label }}</span>
        <span class="campus-pill-status" aria-hidden="true"></span>
      </RouterLink>
    </nav>
    <button class="campus-pill-menu" type="button" :aria-expanded="mobileOpen" aria-label="切换导航菜单" @click="mobileOpen = !mobileOpen">
      <i></i><i></i>
    </button>
    <Transition name="pill-menu-pop">
      <nav v-if="mobileOpen" class="campus-pill-mobile" aria-label="移动端导航">
        <RouterLink v-for="item in items" :key="item.to" :to="destination(item.to)" :class="{ active: route.path === item.to }" @click="mobileOpen = false">{{ item.label }}</RouterLink>
      </nav>
    </Transition>
  </div>
</template>
