<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'

const emit = defineEmits(['close', 'created'])

const formData = ref({ name: '', description: '', category: 'domain' })
const selectedModules = ref([])
const modules = ref([])
const loading = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    await api.createTemplate({ ...formData.value, modules: selectedModules.value })
    emit('created')
  } catch (e) {
    console.error('Failed to create template:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.getModules()
    modules.value = data
  } catch {}
})
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" @click.self="$emit('close')">
      <div class="card w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="sticky top-0 px-6 py-4 flex items-center justify-between border-b" style="background-color: var(--card-bg); border-color: var(--border)">
          <h2 class="text-xl font-bold" style="color: var(--text-primary)">Create Template</h2>
          <button class="btn-ghost text-xl leading-none px-2" type="button" @click="$emit('close')">×</button>
        </div>

        <form @submit.prevent="handleSubmit" class="p-6 space-y-5">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Template Name *</label>
            <input v-model="formData.name" type="text" required class="input" placeholder="Quick Domain Scan" />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Description</label>
            <textarea v-model="formData.description" rows="2" class="input resize-none" placeholder="What does this template do?" />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Category</label>
            <select v-model="formData.category" required class="input">
              <option value="domain">Domain</option>
              <option value="ip">IP</option>
              <option value="email">Email</option>
              <option value="comprehensive">Comprehensive</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--text-secondary)">
              Modules <span class="ml-1" style="color: var(--text-muted)">({{ selectedModules.length }} selected)</span>
            </label>
            <div class="space-y-1 max-h-56 overflow-y-auto pr-1">
              <label v-for="m in modules" :key="m.module_id"
                class="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer border transition-all"
                :style="selectedModules.includes(m.module_id)
                  ? 'border-color: var(--accent); background-color: rgba(59,130,246,0.08)'
                  : 'border-color: var(--border); background-color: transparent'"
              >
                <input type="checkbox" :value="m.module_id" v-model="selectedModules" class="rounded" />
                <div class="flex-1 min-w-0">
                  <span class="text-sm font-medium" style="color: var(--text-primary)">{{ m.display_name }}</span>
                  <span class="ml-2 badge badge-slate text-[10px]">{{ m.category }}</span>
                </div>
              </label>
            </div>
          </div>

          <div class="flex gap-3 pt-2">
            <button type="submit" class="btn-primary flex-1" :disabled="loading || !formData.name || selectedModules.length === 0">
              {{ loading ? 'Creating…' : 'Create Template' }}
            </button>
            <button type="button" class="btn-secondary" @click="$emit('close')">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
