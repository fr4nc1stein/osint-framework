<template>
  <div 
    class="fixed inset-0 bg-white/30 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    @click="$emit('close')"
  >
    <div 
      class="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      @click.stop
    >
      <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-gray-900">Create Template</h2>
        <button 
          @click="$emit('close')" 
          class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
        >
          ×
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Template Name</label>
          <input
            v-model="formData.name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea
            v-model="formData.description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Category</label>
          <select
            v-model="formData.category"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900"
          >
            <option value="domain">Domain</option>
            <option value="ip">IP</option>
            <option value="email">Email</option>
            <option value="comprehensive">Comprehensive</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Select Modules ({{ selectedModules.length }})
          </label>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <label
              v-for="module in modules"
              :key="module.module_id"
              class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
            >
              <input
                type="checkbox"
                :value="module.module_id"
                v-model="selectedModules"
                class="rounded text-primary-600"
              />
              <span class="text-sm text-gray-900">{{ module.display_name }}</span>
            </label>
          </div>
        </div>

        <div class="flex gap-3 pt-4">
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg font-medium"
          >
            {{ loading ? 'Creating...' : 'Create Template' }}
          </button>
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-900"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../api/client';

const emit = defineEmits(['close', 'created']);

const formData = ref({
  name: '',
  description: '',
  category: 'domain',
});

const selectedModules = ref([]);
const modules = ref([]);
const loading = ref(false);

const handleSubmit = async () => {
  loading.value = true;
  try {
    await api.createTemplate({
      ...formData.value,
      modules: selectedModules.value,
    });
    emit('created');
  } catch (error) {
    console.error('Failed to create template:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  try {
    const response = await api.getModules();
    modules.value = response.data;
  } catch (error) {
    console.error('Failed to fetch modules:', error);
  }
});
</script>
