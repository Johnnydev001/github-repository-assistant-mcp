<script setup lang="ts">
import { ref } from 'vue'

const message = ref('')
const messages = ref<Array<{role: string; text: string}>>([])
const loading = ref(false)

async function send() {
  if (!message.value.trim()) return
  messages.value.push({ role: 'user', text: message.value })
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
    messages.value.push({ role: 'assistant', text: data.reply || JSON.stringify(data) })
  } catch (err) {
    messages.value.push({ role: 'assistant', text: 'Error: ' + String(err) })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="chat-container">
    <h1>MCP Assistant (Chat)</h1>
    <div class="messages">
      <div v-for="(m, idx) in messages" :key="idx" :class="['message', m.role]">
        <strong>{{ m.role }}:</strong>
        <div class="text">{{ m.text }}</div>
      </div>
    </div>

    <form @submit.prevent="send" class="input-row">
      <input v-model="message" placeholder="Say something to the MCP server..." />
      <button type="submit" :disabled="loading">Send</button>
    </form>
  </main>
</template>

<style scoped>
.chat-container { max-width: 720px; margin: 2rem auto; font-family: system-ui, sans-serif }
.messages { border: 1px solid #eee; padding: 1rem; min-height: 200px; background: #fafafa }
.message { margin-bottom: 0.75rem }
.message.user { text-align: right }
.message.assistant { text-align: left }
.input-row { display: flex; gap: .5rem; margin-top: .75rem }
input { flex: 1; padding: .5rem }
button { padding: .5rem 1rem }
.text { white-space: pre-wrap; margin-top: .25rem }
</style>
