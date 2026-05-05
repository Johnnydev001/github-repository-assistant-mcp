<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'

const message = ref('')
const messages = ref<Array<{role: string; text: string; ts?: string}>>([])
const loading = ref(false)
const messagesEl = ref<HTMLElement | null>(null as any)

function append(role: string, text: string) {
  messages.value.push({ role, text, ts: new Date().toLocaleTimeString() })
}

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

async function send() {
  if (!message.value.trim()) return
  append('user', message.value)
  const payload = { message: message.value }
  message.value = ''
  loading.value = true
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await resp.json()
    append('assistant', data.reply || JSON.stringify(data))
  } catch (err) {
    append('assistant', 'Error: ' + String(err))
  } finally {
    loading.value = false
    scrollBottom()
  }
}

onMounted(() => scrollBottom())
</script>

<template>
  <main class="chat-container">
    <h1>MCP Assistant</h1>
    <div class="messages" ref="messagesEl">
      <div v-for="(m, idx) in messages" :key="idx" :class="['message', m.role]">
        <div class="meta"><strong>{{ m.role }}</strong> <small>{{ m.ts }}</small></div>
        <div class="text">{{ m.text }}</div>
      </div>
    </div>

    <form @submit.prevent="send" class="input-row">
      <input v-model="message" placeholder="Ask the MCP server..." @keydown.enter.prevent="send" />
      <button type="submit" :disabled="loading">{{ loading ? '...' : 'Send' }}</button>
    </form>
  </main>
</template>

<style scoped>
.chat-container { max-width: 720px; margin: 2rem auto; font-family: system-ui, sans-serif }
.messages { border: 1px solid #eee; padding: 1rem; min-height: 240px; background: #fff; overflow:auto; max-height:60vh }
.message { margin-bottom: 0.75rem; padding: .5rem; border-radius: 6px }
.message.user { background:#e6f7ff; align-self: flex-end }
.message.assistant { background:#f6f6f6; align-self: flex-start }
.meta { font-size: .8rem; color: #666 }
.input-row { display: flex; gap: .5rem; margin-top: .75rem }
input { flex: 1; padding: .5rem; border:1px solid #ddd; border-radius:4px }
button { padding: .5rem 1rem; border-radius:4px }
.text { white-space: pre-wrap; margin-top: .25rem }
</style>
