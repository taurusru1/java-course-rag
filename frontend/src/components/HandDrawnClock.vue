<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const now = ref(new Date())
let timer
const hourAngle = computed(() => ((now.value.getHours() % 12) + now.value.getMinutes() / 60) * 30)
const minuteAngle = computed(() => (now.value.getMinutes() + now.value.getSeconds() / 60) * 6)
const secondAngle = computed(() => now.value.getSeconds() * 6)
const dateLabel = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: 'short', day: 'numeric', weekday: 'short',
}).format(now.value))
const timeLabel = computed(() => new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
}).format(now.value))

onMounted(() => { timer = window.setInterval(() => { now.value = new Date() }, 1000) })
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <aside class="hand-clock" aria-label="当前时间">
    <svg class="hand-clock-face" viewBox="0 0 120 120" role="img" :aria-label="timeLabel">
      <path class="clock-sketch clock-sketch-one" d="M60 7 C88 5 113 29 113 59 C114 89 91 113 60 113 C30 114 7 90 7 60 C6 31 30 8 60 7 Z" />
      <path class="clock-sketch clock-sketch-two" d="M60 10 C88 8 109 32 110 59 C111 87 88 109 61 110 C33 111 10 88 10 60 C9 33 32 11 60 10 Z" />
      <g class="clock-ticks">
        <line v-for="index in 12" :key="index" x1="60" y1="14" x2="60" :y2="index % 3 === 0 ? 21 : 18" :transform="`rotate(${index * 30} 60 60)`" />
      </g>
      <text x="60" y="29">12</text><text x="92" y="64">3</text>
      <text x="60" y="99">6</text><text x="28" y="64">9</text>
      <line class="clock-hand hour" x1="60" y1="60" x2="60" y2="37" :transform="`rotate(${hourAngle} 60 60)`" />
      <line class="clock-hand minute" x1="60" y1="60" x2="60" y2="27" :transform="`rotate(${minuteAngle} 60 60)`" />
      <line class="clock-hand second" x1="60" y1="66" x2="60" y2="23" :transform="`rotate(${secondAngle} 60 60)`" />
      <circle cx="60" cy="60" r="3.2" />
    </svg>
    <div class="hand-clock-copy">
      <time :datetime="now.toISOString()">{{ timeLabel.slice(0, 5) }}</time>
      <span>{{ dateLabel }}</span>
    </div>
  </aside>
</template>
