<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button @click="$router.push('/')" class="text-gray-500 hover:text-gray-700">
              ← Back
            </button>
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ scan?.seed_value || 'Loading...' }}</h1>
              <p class="text-sm text-gray-500">{{ scan?.seed_kind }} scan</p>
            </div>
          </div>
          <div v-if="scan" class="flex items-center gap-3">
            <span class="px-3 py-1 text-sm rounded-full" :class="statusClass(scan.status)">
              {{ scan.status }}
            </span>
            <div class="relative group">
              <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-900">
                Export ▾
              </button>
              <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 hidden group-hover:block z-10">
                <button @click="exportScan('json')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-gray-900">Export JSON</button>
                <button @click="exportScan('csv')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-gray-900">Export CSV</button>
                <button @click="exportScan('graphml')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-gray-900">Export GraphML</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading scan details...
      </div>

      <div v-else-if="scan" class="space-y-6">
        <!-- Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="text-sm text-gray-500 mb-1">Progress</div>
            <div class="text-3xl font-bold text-gray-900">{{ scan.progress }}/{{ scan.total_modules }}</div>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="text-sm text-gray-500 mb-1">Modules</div>
            <div class="text-3xl font-bold text-primary-600">{{ scan.modules.length }}</div>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="text-sm text-gray-500 mb-1">Nodes</div>
            <div class="text-3xl font-bold text-green-600">{{ graphData?.nodes?.length || 0 }}</div>
          </div>
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="text-sm text-gray-500 mb-1">Edges</div>
            <div class="text-3xl font-bold text-gray-900">{{ graphData?.edges?.length || 0 }}</div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
          <div class="border-b border-gray-200">
            <nav class="flex gap-8 px-6">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                class="py-4 border-b-2 font-medium text-sm transition-colors"
                :class="activeTab === tab.id 
                  ? 'border-primary-600 text-primary-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'"
              >
                {{ tab.label }}
              </button>
            </nav>
          </div>

          <!-- Graph Tab -->
          <div v-if="activeTab === 'graph'" class="p-6">
            <GraphVisualization :graph-data="graphData" />
          </div>

          <!-- Events Tab -->
          <div v-if="activeTab === 'events'" class="p-6">
            <div v-if="events.length === 0" class="text-center py-12 text-gray-500">
              No events yet
            </div>
            <div v-else class="space-y-3">
              <div
                v-for="(event, index) in events"
                :key="index"
                class="p-4 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium text-gray-900">{{ event.type }}</span>
                  <span class="text-xs text-gray-500">{{ formatTime(event.timestamp) }}</span>
                </div>
                <pre class="text-xs text-gray-600 overflow-x-auto">{{ JSON.stringify(event, null, 2) }}</pre>
              </div>
            </div>
          </div>

          <!-- Details Tab -->
          <div v-if="activeTab === 'details'" class="p-6">
            <dl class="grid grid-cols-2 gap-4">
              <div>
                <dt class="text-sm font-medium text-gray-500">Scan ID</dt>
                <dd class="mt-1 text-sm text-gray-900 font-mono">{{ scan.id }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Status</dt>
                <dd class="mt-1"><span class="px-2 py-1 text-xs rounded-full" :class="statusClass(scan.status)">{{ scan.status }}</span></dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Created</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ new Date(scan.created_at).toLocaleString() }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Started</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ scan.started_at ? new Date(scan.started_at).toLocaleString() : 'Not started' }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Finished</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ scan.finished_at ? new Date(scan.finished_at).toLocaleString() : 'Not finished' }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500">Modules</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ scan.modules.join(', ') }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useScansStore } from '../stores/scans';
import { api } from '../api/client';
import GraphVisualization from '../components/GraphVisualization.vue';

const route = useRoute();
const scansStore = useScansStore();

const scan = computed(() => scansStore.currentScan);
const loading = computed(() => scansStore.loading);

const activeTab = ref('graph');
const graphData = ref(null);
const events = ref([]);
const ws = ref(null);

const tabs = [
  { id: 'graph', label: 'Graph' },
  { id: 'events', label: 'Events' },
  { id: 'details', label: 'Details' },
];

const statusClass = (status) => {
  const classes = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return classes[status] || 'bg-gray-100 text-gray-800';
};

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString();
};

const loadGraphData = async () => {
  try {
    const response = await api.getScanGraph(route.params.id);
    graphData.value = response.data.graph;
  } catch (error) {
    console.error('Failed to load graph data:', error);
  }
};

const connectWebSocket = () => {
  // Use relative WebSocket URL so it goes through Nginx proxy
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/scan/${route.params.id}`;
  ws.value = new WebSocket(wsUrl);

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    events.value.unshift(data);
    
    // Update scan data on progress
    if (data.type === 'module_complete' || data.type === 'scan_complete') {
      scansStore.fetchScan(route.params.id);
      loadGraphData();
    }
  };

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
};

const exportScan = async (format) => {
  try {
    let response;
    let filename;
    
    if (format === 'json') {
      response = await api.exportJSON(route.params.id);
      filename = `scan_${route.params.id}.json`;
    } else if (format === 'csv') {
      response = await api.exportCSV(route.params.id, 'edges');
      filename = `scan_${route.params.id}_edges.csv`;
    } else if (format === 'graphml') {
      response = await api.exportGraphML(route.params.id);
      filename = `scan_${route.params.id}.graphml`;
    }

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Export failed:', error);
  }
};

onMounted(async () => {
  await scansStore.fetchScan(route.params.id);
  await loadGraphData();
  connectWebSocket();
});

onUnmounted(() => {
  if (ws.value) {
    ws.value.close();
  }
});
</script>
