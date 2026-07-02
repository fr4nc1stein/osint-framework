<script setup>
import { ref, watch } from 'vue'
import { useCasesStore } from '../stores/cases'

const props = defineProps({
  caseData: { type: Object, required: true },
})
const emit = defineEmits(['close', 'saved'])

const casesStore = useCasesStore()
const saving = ref(false)
const error  = ref(null)

const form = ref({})

watch(
  () => props.caseData,
  (c) => {
    form.value = {
      title:           c.title          || '',
      description:     c.description    || '',
      status:          c.status         || 'open',
      priority:        c.priority       || 'medium',
      case_type:       c.case_type      || '',
      assigned_to:     c.assigned_to    || '',
      client:          c.client         || '',
      jurisdiction:    c.jurisdiction   || '',
      target_name:     c.target_name    || '',
      target_aliases:  (c.target_aliases || []).join(', '),
      target_location: c.target_location|| '',
      target_dob:      c.target_dob     || '',
      tags:            (c.tags || []).join(', '),
      closed_reason:   c.closed_reason  || '',
    }
  },
  { immediate: true }
)

async function save() {
  saving.value = true
  error.value  = null
  try {
    const payload = {
      ...form.value,
      target_aliases: form.value.target_aliases
        ? form.value.target_aliases.split(',').map(s => s.trim()).filter(Boolean)
        : [],
      tags: form.value.tags
        ? form.value.tags.split(',').map(s => s.trim()).filter(Boolean)
        : [],
      case_type:       form.value.case_type       || null,
      assigned_to:     form.value.assigned_to     || null,
      client:          form.value.client          || null,
      jurisdiction:    form.value.jurisdiction    || null,
      target_name:     form.value.target_name     || null,
      target_location: form.value.target_location || null,
      target_dob:      form.value.target_dob      || null,
      closed_reason:   form.value.closed_reason   || null,
    }
    await casesStore.updateCase(props.caseData.id, payload)
    emit('saved')
    emit('close')
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="$emit('close')">
      <div class="card w-full max-w-2xl mx-4 flex flex-col max-h-[90vh]">

        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b shrink-0" style="border-color: var(--border)">
          <h2 class="text-lg font-semibold" style="color: var(--text-primary)">Edit Case</h2>
          <button class="btn-ghost p-1 rounded" @click="$emit('close')">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Body -->
        <div class="overflow-y-auto flex-1 px-6 py-5 space-y-5">

          <!-- Error -->
          <div v-if="error" class="text-sm px-3 py-2 rounded" style="background-color: rgba(239,68,68,0.12); color: #f87171">
            {{ error }}
          </div>

          <!-- Title -->
          <div>
            <label class="form-label">Title *</label>
            <input v-model="form.title" class="input" placeholder="Investigation title" required />
          </div>

          <!-- Description -->
          <div>
            <label class="form-label">Description</label>
            <textarea v-model="form.description" class="input h-20 resize-none" placeholder="What are you investigating?" />
          </div>

          <!-- Status / Priority / Case Type -->
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="form-label">Status</label>
              <select v-model="form.status" class="input">
                <option value="open">Open</option>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <div>
              <label class="form-label">Severity</label>
              <select v-model="form.priority" class="input">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label class="form-label">Case Type</label>
              <input v-model="form.case_type" class="input" placeholder="e.g. fraud, apt" />
            </div>
          </div>

          <!-- Closed reason (only visible when status is closed/archived) -->
          <div v-if="form.status === 'closed' || form.status === 'archived'">
            <label class="form-label">Reason for Closing</label>
            <input v-model="form.closed_reason" class="input" placeholder="Investigation complete, no findings, etc." />
          </div>

          <!-- Assigned / Client / Jurisdiction -->
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="form-label">Assigned To</label>
              <input v-model="form.assigned_to" class="input" placeholder="Analyst name" />
            </div>
            <div>
              <label class="form-label">Client</label>
              <input v-model="form.client" class="input" placeholder="Client or org" />
            </div>
            <div>
              <label class="form-label">Jurisdiction</label>
              <input v-model="form.jurisdiction" class="input" placeholder="e.g. US, EU" />
            </div>
          </div>

          <!-- Target section -->
          <div class="pt-1">
            <p class="text-xs font-semibold uppercase tracking-wider mb-3" style="color: var(--text-muted)">Target Information</p>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="form-label">Target Name</label>
                  <input v-model="form.target_name" class="input" placeholder="Full name or entity" />
                </div>
                <div>
                  <label class="form-label">Aliases (comma separated)</label>
                  <input v-model="form.target_aliases" class="input" placeholder="alias1, alias2" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="form-label">Location</label>
                  <input v-model="form.target_location" class="input" placeholder="City, Country" />
                </div>
                <div>
                  <label class="form-label">Date of Birth</label>
                  <input v-model="form.target_dob" type="date" class="input" />
                </div>
              </div>
            </div>
          </div>

          <!-- Tags -->
          <div>
            <label class="form-label">Tags (comma separated)</label>
            <input v-model="form.tags" class="input" placeholder="malware, phishing, apt29" />
          </div>

        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 px-6 py-4 border-t shrink-0" style="border-color: var(--border)">
          <button class="btn-secondary" @click="$emit('close')">Cancel</button>
          <button class="btn-primary" :disabled="!form.title || saving" @click="save">
            <span v-if="saving">Saving…</span>
            <span v-else>Save Changes</span>
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>
