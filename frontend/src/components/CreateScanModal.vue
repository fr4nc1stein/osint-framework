<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useModulesStore } from '../stores/modules'
import { useScansStore } from '../stores/scans'

const props = defineProps({
  defaultCaseId: { type: String, default: null },
  defaultTarget:  { type: String, default: '' },
  defaultKind:    { type: String, default: 'domain' },
  parentScanId:   { type: String, default: null },
  suggestedModules: { type: Array, default: () => [] },
  sourceNode: { type: Object, default: null },
})

const emit = defineEmits(['close', 'created'])
const router = useRouter()
const modulesStore = useModulesStore()
const scansStore = useScansStore()

const formData = ref({
  seed_value: props.defaultTarget,
  seed_kind: props.defaultKind,
})
const selectedModules = ref([...props.suggestedModules])
const loading = ref(false)
const error = ref(null)

const compatibleModules = computed(() => modulesStore.modules.filter(module => (
  (module.accepts || []).map(kind => kind.toLowerCase()).includes(formData.value.seed_kind)
)))
const modulesByCategory = computed(() => {
  const grouped = {}
  for (const module of compatibleModules.value) {
    if (!grouped[module.category]) grouped[module.category] = []
    grouped[module.category].push(module)
  }
  return grouped
})

watch(() => formData.value.seed_kind, () => {
  const compatibleIds = new Set(compatibleModules.value.map(module => module.module_id))
  selectedModules.value = selectedModules.value.filter(moduleId => compatibleIds.has(moduleId))
})

async function handleSubmit() {
  if (selectedModules.value.length === 0) {
    error.value = 'Please select at least one module'
    return
  }
  loading.value = true
  error.value = null
  try {
    const payload = {
      ...formData.value,
      modules: selectedModules.value,
    }
    if (props.defaultCaseId) payload.case_id = props.defaultCaseId
    if (props.parentScanId) payload.parent_scan_id = props.parentScanId
    if (props.sourceNode) {
      payload.launch_source = 'case_node'
      payload.source_node_type = props.sourceNode.node_type
      payload.source_node_id = props.sourceNode.node_id
      payload.source_node_label = props.sourceNode.label
      payload.source_context = props.sourceNode.context || {}
    }

    const scan = await scansStore.createScan(payload)
    emit('created', scan.id)
    router.push(`/scan/${scan.id}`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create scan'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (modulesStore.modules.length === 0) modulesStore.fetchModules()
})
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" @click.self="$emit('close')">
      <div class="card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="sticky top-0 px-6 py-4 flex items-center justify-between border-b" style="background-color: var(--card-bg); border-color: var(--border)">
          <h2 class="text-xl font-bold" style="color: var(--text-primary)">Create New Scan</h2>
          <button class="btn-ghost text-xl leading-none px-2" type="button" @click="$emit('close')">×</button>
        </div>

        <form @submit.prevent="handleSubmit" class="p-6 space-y-5">
          <!-- Target -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Target</label>
            <input v-model="formData.seed_value" type="text" required class="input"
              placeholder="example.com, 8.8.8.8, email@example.com" />
          </div>

          <!-- Type -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--text-secondary)">Target Type</label>
            <select v-model="formData.seed_kind" required class="input">
              <option value="domain">Domain</option>
              <option value="ip">IP Address</option>
              <option value="email">Email</option>
              <option value="url">URL</option>
              <option value="phone">Phone</option>
              <option value="username">Username</option>
              <option value="bitcoin">Bitcoin</option>
            </select>
          </div>

          <!-- Parent scan info -->
          <div v-if="parentScanId" class="rounded-lg px-3 py-2 text-sm" style="background-color: var(--bg-tertiary); color: var(--text-secondary)">
            This will be a child scan derived from the parent graph node.
          </div>

          <div v-if="sourceNode" class="rounded-lg border px-3 py-2 text-sm space-y-1" style="border-color: var(--border); background-color: var(--bg-tertiary); color: var(--text-secondary)">
            <div class="flex flex-wrap items-center gap-2">
              <span class="badge badge-purple text-[10px]">case node</span>
              <span class="font-medium break-all" style="color: var(--text-primary)">{{ sourceNode.label }}</span>
            </div>
            <p class="text-xs" style="color: var(--text-muted)">
              Source metadata will be saved with this scan.
            </p>
          </div>

          <!-- Modules -->
          <div>
            <label class="block text-sm font-medium mb-2" style="color: var(--text-secondary)">
              Modules <span class="ml-1" style="color: var(--text-muted)">({{ selectedModules.length }} selected)</span>
            </label>
            <div v-if="modulesStore.loading" class="text-center py-4" style="color: var(--text-muted)">
              Loading modules…
            </div>
            <div v-else-if="compatibleModules.length === 0" class="rounded-lg border p-3 text-sm" style="border-color: var(--border); color: var(--text-muted); background-color: var(--bg-primary)">
              No scan modules currently support this target type.
            </div>
            <div v-else class="space-y-4">
              <div v-for="(mods, category) in modulesByCategory" :key="category">
                <div class="text-xs font-semibold uppercase mb-2" style="color: var(--text-muted)">{{ category }}</div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <label v-for="m in mods" :key="m.module_id"
                    class="flex items-start gap-2 p-3 rounded-lg cursor-pointer border transition-all"
                    :style="selectedModules.includes(m.module_id)
                      ? 'border-color: var(--accent); background-color: rgba(59,130,246,0.08)'
                      : 'border-color: var(--border); background-color: var(--bg-primary)'"
                  >
                    <input type="checkbox" :value="m.module_id" v-model="selectedModules" class="mt-0.5 rounded" />
                    <div class="flex-1 min-w-0">
                      <div class="text-sm font-medium" style="color: var(--text-primary)">{{ m.display_name }}</div>
                      <div class="text-xs mt-0.5" style="color: var(--text-muted)">{{ m.description }}</div>
                      <span v-if="m.requires_api_key" class="badge badge-amber text-[10px] mt-1">API key</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div v-if="error" class="text-sm text-red-400">{{ error }}</div>

          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button type="submit" class="btn-primary flex-1" :disabled="loading || selectedModules.length === 0">
              {{ loading ? 'Creating…' : 'Create Scan' }}
            </button>
            <button type="button" class="btn-secondary" @click="$emit('close')">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
