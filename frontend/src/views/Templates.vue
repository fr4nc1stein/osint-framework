<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Scan Templates</h1>
            <p class="text-sm text-gray-500">Reusable scan configurations</p>
          </div>
          <button 
            @click="showCreateModal = true"
            class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + New Template
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading templates...
      </div>

      <div v-else-if="templates.length === 0" class="text-center py-12 text-gray-500">
        No templates yet. Create your first template!
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="template in templates"
          :key="template.id"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">{{ template.name }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ template.description }}</p>
            </div>
            <span class="px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-800">
              {{ template.category }}
            </span>
          </div>

          <div class="mb-4">
            <div class="text-xs text-gray-500 mb-2">Modules ({{ template.modules.length }})</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="module in template.modules.slice(0, 5)"
                :key="module"
                class="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {{ module }}
              </span>
              <span v-if="template.modules.length > 5" class="px-2 py-1 text-xs text-gray-500">
                +{{ template.modules.length - 5 }} more
              </span>
            </div>
          </div>

          <div class="flex gap-2">
            <button
              @click="useTemplate(template)"
              class="flex-1 bg-primary-600 hover:bg-primary-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Use Template
            </button>
            <button
              @click="deleteTemplate(template.id)"
              class="px-3 py-2 border border-red-300 text-red-600 hover:bg-red-50 rounded-lg text-sm transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Create Template Modal -->
    <CreateTemplateModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="onTemplateCreated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '../api/client';
import CreateTemplateModal from '../components/CreateTemplateModal.vue';

const router = useRouter();

const templates = ref([]);
const loading = ref(false);
const showCreateModal = ref(false);

const fetchTemplates = async () => {
  loading.value = true;
  try {
    const response = await api.getTemplates();
    templates.value = response.data;
  } catch (error) {
    console.error('Failed to fetch templates:', error);
  } finally {
    loading.value = false;
  }
};

const useTemplate = (template) => {
  // Navigate to dashboard with template pre-selected
  router.push({ 
    path: '/', 
    query: { template: template.id } 
  });
};

const deleteTemplate = async (id) => {
  if (!confirm('Are you sure you want to delete this template?')) return;
  
  try {
    await api.deleteTemplate(id);
    templates.value = templates.value.filter(t => t.id !== id);
  } catch (error) {
    console.error('Failed to delete template:', error);
  }
};

const onTemplateCreated = () => {
  showCreateModal.value = false;
  fetchTemplates();
};

onMounted(() => {
  fetchTemplates();
});
</script>
