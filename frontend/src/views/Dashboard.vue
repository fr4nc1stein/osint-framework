<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">OSIF v2.0</h1>
            <p class="text-sm text-gray-500">Open Source Intelligence Framework</p>
          </div>
          <button 
            @click="showCreateModal = true"
            class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + New Scan
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div class="text-sm text-gray-500 mb-1">Total Scans</div>
          <div class="text-3xl font-bold text-gray-900">{{ scans.length }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div class="text-sm text-gray-500 mb-1">Running</div>
          <div class="text-3xl font-bold text-primary-600">{{ runningScans }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div class="text-sm text-gray-500 mb-1">Completed</div>
          <div class="text-3xl font-bold text-green-600">{{ completedScans }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div class="text-sm text-gray-500 mb-1">Modules</div>
          <div class="text-3xl font-bold text-gray-900">{{ modulesStore.modules.length }}</div>
        </div>
      </div>

      <!-- Scans List -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200">
        <div class="px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Recent Scans</h2>
        </div>
        
        <div v-if="loading" class="p-8 text-center text-gray-500">
          Loading scans...
        </div>

        <div v-else-if="scans.length === 0" class="p-8 text-center text-gray-500">
          No scans yet. Create your first scan to get started!
        </div>

        <div v-else class="divide-y divide-gray-200">
          <div 
            v-for="scan in scans" 
            :key="scan.id"
            @click="$router.push(`/scan/${scan.id}`)"
            class="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3">
                  <span class="text-lg font-medium text-gray-900">{{ scan.seed_value }}</span>
                  <span class="px-2 py-1 text-xs rounded-full" :class="statusClass(scan.status)">
                    {{ scan.status }}
                  </span>
                </div>
                <div class="mt-1 text-sm text-gray-500">
                  {{ scan.modules.length }} modules • Created {{ formatDate(scan.created_at) }}
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm font-medium text-gray-900">
                  {{ scan.progress }}/{{ scan.total_modules }}
                </div>
                <div class="text-xs text-gray-500">Progress</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Create Scan Modal -->
    <CreateScanModal 
      v-if="showCreateModal" 
      @close="showCreateModal = false"
      @created="onScanCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useScansStore } from '../stores/scans';
import { useModulesStore } from '../stores/modules';
import CreateScanModal from '../components/CreateScanModal.vue';

const scansStore = useScansStore();
const modulesStore = useModulesStore();
const showCreateModal = ref(false);

const scans = computed(() => scansStore.scans);
const loading = computed(() => scansStore.loading);

const runningScans = computed(() => 
  scans.value.filter(s => s.status === 'running' || s.status === 'pending').length
);

const completedScans = computed(() => 
  scans.value.filter(s => s.status === 'completed').length
);

const statusClass = (status) => {
  const classes = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return classes[status] || 'bg-gray-100 text-gray-800';
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
};

const onScanCreated = (scan) => {
  showCreateModal.value = false;
  scansStore.fetchScans();
};

onMounted(() => {
  scansStore.fetchScans();
  modulesStore.fetchModules();
});
</script>
