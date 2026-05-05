<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Transition } from '@headlessui/vue'

const STORAGE_KEY = 'mcp_chat_v1'

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

// Persistence
onMounted(() => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) messages.value = JSON.parse(raw)
  } catch (e) {
    console.warn('Failed to load chat history', e)
  }
  scrollBottom()
})

watch(messages, (v) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(v))
  } catch (e) {
    console.warn('Failed to save chat history', e)
  }
}, { deep: true })

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
    <h1 class="text-2xl font-semibold mb-4">MCP Assistant</h1>
    <div class="messages" ref="messagesEl">
      <div v-for="(m, idx) in messages" :key="idx">
        <Transition
          enter="transform transition ease-out duration-200"
          enter-from="opacity-0 translate-y-2"
          enter-to="opacity-100 translate-y-0"
        >
          <div :class="['message', m.role, 'p-3 my-2 rounded-lg']">
            <div class="meta text-sm text-gray-500"><strong>{{ m.role }}</strong> <small>{{ m.ts }}</small></div>
            <div class="text mt-1">{{ m.text }}</div>
          </div>
        </Transition>
      </div>
    </div>

    <form @submit.prevent="send" class="input-row mt-4 flex">
      <input v-model="message" placeholder="Ask the MCP server..." @keydown.enter.prevent="send" class="flex-1 p-2 border rounded-md" />
      <button type="submit" :disabled="loading" class="ml-3 px-4 py-2 bg-blue-600 text-white rounded-md">{{ loading ? '...' : 'Send' }}</button>
    </form>
  </main>
</template>

<style scoped>
.chat-container { max-width: 720px; margin: 2rem auto; font-family: system-ui, sans-serif }
.messages { border: 1px solid #eee; padding: 1rem; min-height: 240px; background: #fff; overflow:auto; max-height:60vh }
.message.user { background:#e6f7ff; align-self: flex-end }
.message.assistant { background:#f6f6f6; align-self: flex-start }
.meta { font-size: .8rem; color: #666 }
.input-row input { flex:1 }
</style>
