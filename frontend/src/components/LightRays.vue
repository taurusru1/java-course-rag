<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Mesh, Program, Renderer, Triangle } from 'ogl'

const props = defineProps({
  raysOrigin: { type: String, default: 'top-center' },
  raysColor: { type: String, default: '#ffffff' },
  raysSpeed: { type: Number, default: 1 },
  lightSpread: { type: Number, default: 1 },
  rayLength: { type: Number, default: 2 },
  pulsating: Boolean,
  fadeDistance: { type: Number, default: 1 },
  saturation: { type: Number, default: 1 },
  followMouse: { type: Boolean, default: true },
  mouseInfluence: { type: Number, default: .1 },
  noiseAmount: { type: Number, default: 0 },
  distortion: { type: Number, default: 0 },
})

const container = ref(null)
let renderer
let mesh
let uniforms
let frame = 0
let resizeObserver
let mouseFrame = 0
const mouse = { x: .5, y: .5 }
const smoothMouse = { x: .5, y: .5 }
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')

const vertex = `attribute vec2 position;varying vec2 vUv;void main(){vUv=position*.5+.5;gl_Position=vec4(position,0.,1.);}`
const fragment = `precision highp float;
uniform float iTime;uniform vec2 iResolution;uniform vec2 rayPos;uniform vec2 rayDir;uniform vec3 raysColor;
uniform float raysSpeed;uniform float lightSpread;uniform float rayLength;uniform float pulsating;uniform float fadeDistance;
uniform float saturation;uniform vec2 mousePos;uniform float mouseInfluence;uniform float noiseAmount;uniform float distortion;
varying vec2 vUv;
float rand(vec2 st){return fract(sin(dot(st.xy,vec2(12.9898,78.233)))*43758.5453);}
float rayStrength(vec2 source,vec2 reference,vec2 coord,float seedA,float seedB,float speed){
  vec2 delta=coord-source;float angle=dot(normalize(delta),reference);
  angle+=distortion*sin(iTime*2.+length(delta)*.01)*.2;
  float spread=pow(max(angle,0.),1./max(lightSpread,.001));
  float distance=length(delta);float maxDistance=iResolution.x*rayLength;
  float lengthFalloff=clamp((maxDistance-distance)/maxDistance,0.,1.);
  float fade=clamp((iResolution.x*fadeDistance-distance)/(iResolution.x*fadeDistance),.5,1.);
  float pulse=pulsating>.5?.8+.2*sin(iTime*speed*3.):1.;
  float strength=clamp((.45+.15*sin(angle*seedA+iTime*speed))+(.3+.2*cos(-angle*seedB+iTime*speed)),0.,1.);
  return strength*lengthFalloff*fade*spread*pulse;
}
void main(){
  vec2 coord=vec2(gl_FragCoord.x,iResolution.y-gl_FragCoord.y);vec2 direction=rayDir;
  if(mouseInfluence>0.){vec2 mouseDirection=normalize(mousePos*iResolution.xy-rayPos);direction=normalize(mix(rayDir,mouseDirection,mouseInfluence));}
  vec4 color=vec4(1.)*rayStrength(rayPos,direction,coord,36.2214,21.11349,1.5*raysSpeed)*.5;
  color+=vec4(1.)*rayStrength(rayPos,direction,coord,22.3991,18.0234,1.1*raysSpeed)*.4;
  if(noiseAmount>0.)color.rgb*=1.-noiseAmount+noiseAmount*rand(coord*.01+iTime*.1);
  float brightness=1.-coord.y/iResolution.y;color.rgb*=vec3(.1+brightness*.8,.3+brightness*.6,.5+brightness*.5);
  float gray=dot(color.rgb,vec3(.299,.587,.114));color.rgb=mix(vec3(gray),color.rgb,saturation)*raysColor;
  gl_FragColor=color;
}`

const rgb = value => {
  const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(value)
  return match ? [1, 2, 3].map(index => parseInt(match[index], 16) / 255) : [1, 1, 1]
}

const placement = (origin, width, height) => {
  const outside = .2
  const values = {
    'top-left': [[0, -outside * height], [0, 1]],
    'top-right': [[width, -outside * height], [0, 1]],
    left: [[-outside * width, .5 * height], [1, 0]],
    right: [[(1 + outside) * width, .5 * height], [-1, 0]],
    'bottom-left': [[0, (1 + outside) * height], [0, -1]],
    'bottom-center': [[.5 * width, (1 + outside) * height], [0, -1]],
    'bottom-right': [[width, (1 + outside) * height], [0, -1]],
  }
  return values[origin] || [[.5 * width, -outside * height], [0, 1]]
}

const resize = () => {
  if (!container.value || !renderer || !uniforms) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  renderer.setSize(width, height)
  const dpr = renderer.dpr
  uniforms.iResolution.value = [width * dpr, height * dpr]
  ;[uniforms.rayPos.value, uniforms.rayDir.value] = placement(props.raysOrigin, width * dpr, height * dpr)
}

const render = time => {
  if (!renderer || !mesh) return
  uniforms.iTime.value = reduceMotion.matches ? 0 : time * .001
  if (props.followMouse && !reduceMotion.matches) {
    smoothMouse.x = smoothMouse.x * .92 + mouse.x * .08
    smoothMouse.y = smoothMouse.y * .92 + mouse.y * .08
    uniforms.mousePos.value = [smoothMouse.x, smoothMouse.y]
  }
  renderer.render({ scene: mesh })
  if (!reduceMotion.matches) frame = requestAnimationFrame(render)
}

const trackMouse = event => {
  if (!container.value || mouseFrame) return
  mouseFrame = requestAnimationFrame(() => {
    const rect = container.value.getBoundingClientRect()
    mouse.x = (event.clientX - rect.left) / rect.width
    mouse.y = (event.clientY - rect.top) / rect.height
    mouseFrame = 0
  })
}

const updateUniforms = () => {
  if (!uniforms) return
  uniforms.raysColor.value = rgb(props.raysColor)
  uniforms.raysSpeed.value = props.raysSpeed
  uniforms.lightSpread.value = props.lightSpread
  uniforms.rayLength.value = props.rayLength
  uniforms.pulsating.value = props.pulsating ? 1 : 0
  uniforms.fadeDistance.value = props.fadeDistance
  uniforms.saturation.value = props.saturation
  uniforms.mouseInfluence.value = props.mouseInfluence
  uniforms.noiseAmount.value = props.noiseAmount
  uniforms.distortion.value = props.distortion
  resize()
}

onMounted(async () => {
  await nextTick()
  if (!container.value) return
  renderer = new Renderer({ dpr: Math.min(devicePixelRatio || 1, 2), alpha: true, antialias: false, powerPreference: 'high-performance' })
  const gl = renderer.gl
  gl.canvas.style.width = '100%'
  gl.canvas.style.height = '100%'
  container.value.appendChild(gl.canvas)
  uniforms = {
    iTime: { value: 0 }, iResolution: { value: [1, 1] }, rayPos: { value: [0, 0] }, rayDir: { value: [0, 1] },
    raysColor: { value: rgb(props.raysColor) }, raysSpeed: { value: props.raysSpeed }, lightSpread: { value: props.lightSpread },
    rayLength: { value: props.rayLength }, pulsating: { value: props.pulsating ? 1 : 0 }, fadeDistance: { value: props.fadeDistance },
    saturation: { value: props.saturation }, mousePos: { value: [.5, .5] }, mouseInfluence: { value: props.mouseInfluence },
    noiseAmount: { value: props.noiseAmount }, distortion: { value: props.distortion },
  }
  mesh = new Mesh(gl, { geometry: new Triangle(gl), program: new Program(gl, { vertex, fragment, uniforms }) })
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(container.value)
  if (props.followMouse) window.addEventListener('mousemove', trackMouse, { passive: true })
  resize()
  frame = requestAnimationFrame(render)
})

watch(() => [props.raysOrigin, props.raysColor, props.raysSpeed, props.lightSpread, props.rayLength, props.pulsating, props.fadeDistance, props.saturation, props.mouseInfluence, props.noiseAmount, props.distortion], updateUniforms)

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  cancelAnimationFrame(mouseFrame)
  resizeObserver?.disconnect()
  window.removeEventListener('mousemove', trackMouse)
  try { renderer?.gl.getExtension('WEBGL_lose_context')?.loseContext() } catch {}
  renderer = null
  mesh = null
  uniforms = null
})
</script>

<template><div ref="container" class="light-rays" aria-hidden="true"></div></template>

<style scoped>
.light-rays{position:absolute;inset:0;overflow:hidden;pointer-events:none}
</style>
