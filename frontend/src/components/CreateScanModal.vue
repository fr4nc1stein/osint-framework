<template>
  <div 
    class="fixed inset-0 bg-white/30 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    @click="$emit('close')"
  >
    <div 
      class="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      @click.stop
    >
      <!-- Header -->
      <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-gray-900">Create New Scan</h2>
        <button 
          @click="$emit('close')" 
          class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          type="button"
        >
          ×
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
        <!-- Target -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Target
          </label>
          <input
            v-model="formData.seed_value"
            type="text"
            required
            placeholder="example.com, 8.8.8.8, email@example.com"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
          />
        </div>

        <!-- Target Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Target Type
          </label>
          <select
            v-model="formData.seed_kind"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
          >
            <option value="domain">Domain</option>
            <option value="ip">IP Address</option>
            <option value="email">Email</option>
          </select>
        </div>

        <!-- Modules -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Select Modules ({{ selectedModules.length }})
          </label>
          
          <div v-if="modulesStore.loading" class="text-center py-4 text-gray-500">
            Loading modules...
          </div>

          <div v-else class="space-y-4">
            <div v-for="(modules, category) in modulesByCategory" :key="category">
              <div class="text-xs font-semibold text-gray-500 uppercase mb-2">
                {{ category }}
              </div>
              <div class="grid grid-cols-2 gap-2">
                <label
                  v-for="module in modules"
                  :key="module.module_id"
                  class="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="module.module_id"
                    v-model="selectedModules"
                    class="rounded text-primary-600 focus:ring-primary-500"
                  />
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900">{{ module.display_name }}</div>
                    <div class="text-xs text-gray-500">{{ module.description }}</div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4">
          <button
            type="submit"
            :disabled="loading || selectedModules.length === 0"
            class="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            {{ loading ? 'Creating...' : 'Create Scan' }}
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-900"
          >
            Cancel
          </button>
        </div>

        <div v-if="error" class="text-sm text-red-600">
          {{ error }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useModulesStore } from '../stores/modules';
import { useScansStore } from '../stores/scans';

const emit = defineEmits(['close', 'created']);

const modulesStore = useModulesStore();
const scansStore = useScansStore();

const formData = ref({
  seed_value: '',
  seed_kind: 'domain',
});

const selectedModules = ref([]);
const loading = ref(false);
const error = ref(null);

const modulesByCategory = computed(() => modulesStore.modulesByCategory);

const handleSubmit = async () => {
  if (selectedModules.value.length === 0) {
    error.value = 'Please select at least one module';
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const scan = await scansStore.createScan({
      ...formData.value,
      modules: selectedModules.value,
    });
    emit('created', scan);
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create scan';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (modulesStore.modules.length === 0) {
    modulesStore.fetchModules();
  }
});
</script>
