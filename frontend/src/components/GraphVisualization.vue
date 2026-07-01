<template>
  <div>
    <div v-if="!graphData || graphData.nodes.length === 0" class="text-center py-12 text-gray-500">
      No graph data available yet
    </div>
    <div v-else>
      <div ref="cyContainer" class="w-full h-[600px] border border-gray-200 rounded-lg"></div>
      
      <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-xs text-gray-500 mb-1">Total Nodes</div>
          <div class="text-2xl font-bold text-gray-900">{{ graphData.nodes.length }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-xs text-gray-500 mb-1">Total Edges</div>
          <div class="text-2xl font-bold text-gray-900">{{ graphData.edges.length }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-xs text-gray-500 mb-1">Node Types</div>
          <div class="text-2xl font-bold text-gray-900">{{ uniqueNodeTypes }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-xs text-gray-500 mb-1">Relationships</div>
          <div class="text-2xl font-bold text-gray-900">{{ uniqueRelationships }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import cytoscape from 'cytoscape';

const props = defineProps({
  graphData: {
    type: Object,
    default: null,
  },
});

const cyContainer = ref(null);
let cy = null;

const uniqueNodeTypes = computed(() => {
  if (!props.graphData) return 0;
  const types = new Set(props.graphData.nodes.map(n => n.kind));
  return types.size;
});

const uniqueRelationships = computed(() => {
  if (!props.graphData) return 0;
  const rels = new Set(props.graphData.edges.map(e => e.relationship));
  return rels.size;
});

const nodeColors = {
  domain: '#3b82f6',
  ip: '#10b981',
  email: '#f59e0b',
  organization: '#8b5cf6',
  server: '#ec4899',
  asn: '#6366f1',
  reputation: '#ef4444',
  category: '#14b8a6',
  breach: '#dc2626',
  threat: '#991b1b',
};

const initGraph = () => {
  if (!cyContainer.value || !props.graphData) return;

  const elements = [
    ...props.graphData.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        kind: node.kind,
        value: node.value,
      },
    })),
    ...props.graphData.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.relationship,
        confidence: edge.confidence,
      },
    })),
  ];

  cy = cytoscape({
    container: cyContainer.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele) => nodeColors[ele.data('kind')] || '#6b7280',
          'label': 'data(label)',
          'color': '#374151',
          'text-valign': 'bottom',
          'text-halign': 'center',
          'font-size': '10px',
          'width': 30,
          'height': 30,
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#d1d5db',
          'target-arrow-color': '#d1d5db',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '8px',
          'text-rotation': 'autorotate',
          'text-margin-y': -10,
        },
      },
    ],
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 500,
      nodeRepulsion: 8000,
      idealEdgeLength: 100,
    },
  });

  // Add click handler
  cy.on('tap', 'node', (evt) => {
    const node = evt.target;
    console.log('Node clicked:', node.data());
  });
};

watch(() => props.graphData, () => {
  if (cy) {
    cy.destroy();
  }
  initGraph();
}, { deep: true });

onMounted(() => {
  initGraph();
});
</script>
