<script setup>
import { useRoute } from 'vue-router'
import SideRays from './components/SideRays.vue'

const route = useRoute()
</script>

<template>
  <SideRays v-if="route.path !== '/login'" />
  <RouterView />
</template>
