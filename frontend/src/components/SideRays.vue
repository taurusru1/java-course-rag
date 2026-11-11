<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const canvas = ref(null)
let frame = 0
let resizeObserver
let reduceMotion

const colors = ['#315a82', '#b79a68']
const speed = 1.25
const intensity = 1.18
const spread = 2.15
const tilt = 3
const saturation = 0.92
const blend = 0.56
const falloff = 1.9

const hexToRgb = hex => {
  const value = Number.parseInt(hex.slice(1), 16)
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255]
}

const draw = time => {
  const target = canvas.value
  if (!target) return
  const context = target.getContext('2d')
  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  const width = target.clientWidth
  const height = target.clientHeight
  const pixelWidth = Math.round(width * ratio)
  const pixelHeight = Math.round(height * ratio)
  if (target.width !== pixelWidth || target.height !== pixelHeight) {
    target.width = pixelWidth
    target.height = pixelHeight
  }
  context.setTransform(ratio, 0, 0, ratio, 0, 0)
  context.clearRect(0, 0, width, height)

  const diagonal = Math.hypot(width, height) * 1.3
  const phase = reduceMotion.matches ? 0 : time * 0.00032 * speed
  const originX = width * (1.035 + Math.sin(phase * 0.72) * 0.018)
  const originY = height * (-0.035 + Math.cos(phase * 0.58) * 0.018)
  const [gold, blue] = colors.map(hexToRgb)

  context.globalCompositeOperation = 'source-over'
  for (let index = 0; index < 12; index += 1) {
    const wave = Math.sin(phase + index * 1.37) * 0.17
    const base = (Math.PI * (0.545 + index * 0.027 * spread)) + tilt * 0.008
    const angle = base + wave
    const rayWidth = (0.044 + (index % 4) * 0.011) * spread
    const start = { x: originX, y: originY }
    const left = {
      x: originX + Math.cos(angle - rayWidth) * diagonal,
      y: originY + Math.sin(angle - rayWidth) * diagonal,
    }
    const right = {
      x: originX + Math.cos(angle + rayWidth) * diagonal,
      y: originY + Math.sin(angle + rayWidth) * diagonal,
    }
    const mix = (Math.sin(index * 1.71 + phase * 0.7) + 1) / 2
    const rgb = gold.map((value, channel) => Math.round(value * (1 - mix) + blue[channel] * mix))
    const breathe = 0.72 + (Math.sin(phase * 1.35 + index * 0.83) + 1) * 0.18
    const alpha = (0.082 + (index % 3) * 0.02) * intensity * saturation * blend * breathe
    const gradient = context.createRadialGradient(originX, originY, 0, originX, originY, diagonal)
    gradient.addColorStop(0, `rgba(${rgb.join(',')},${alpha})`)
    gradient.addColorStop(Math.min(0.68, 0.24 * falloff), `rgba(${rgb.join(',')},${alpha * 0.62})`)
    gradient.addColorStop(1, `rgba(${rgb.join(',')},0)`)
    context.beginPath()
    context.moveTo(start.x, start.y)
    context.lineTo(left.x, left.y)
    context.lineTo(right.x, right.y)
    context.closePath()
    context.fillStyle = gradient
    context.fill()
  }

  if (!reduceMotion.matches) frame = window.requestAnimationFrame(draw)
}

const restart = () => {
  window.cancelAnimationFrame(frame)
  draw(performance.now())
}

onMounted(() => {
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
  reduceMotion.addEventListener('change', restart)
  resizeObserver = new ResizeObserver(restart)
  resizeObserver.observe(document.documentElement)
  restart()
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(frame)
  resizeObserver?.disconnect()
  reduceMotion?.removeEventListener('change', restart)
})
</script>

<template>
  <canvas ref="canvas" class="side-rays" aria-hidden="true"></canvas>
</template>
