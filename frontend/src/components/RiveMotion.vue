<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { Alignment, Fit, Layout, Rive } from '@rive-app/canvas'

const props = defineProps({
  src: { type: String, required: true },
  label: { type: String, default: '' },
})

const canvas = ref(null)
let rive = null
let observer = null

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  rive = new Rive({
    src: props.src,
    canvas: canvas.value,
    autoplay: true,
    layout: new Layout({ fit: Fit.Contain, alignment: Alignment.Center }),
    onLoad: () => rive?.resizeDrawingSurfaceToCanvas(),
  })
  observer = new ResizeObserver(() => rive?.resizeDrawingSurfaceToCanvas())
  observer.observe(canvas.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  rive?.cleanup()
})
</script>

<template>
  <canvas ref="canvas" class="rive-canvas" :aria-label="label" :aria-hidden="!label" />
</template>
