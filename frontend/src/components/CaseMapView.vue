<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AlertTriangle, Building2, Crosshair, FileImage, LocateFixed, MapPin, Route, Search, ShieldCheck, UserPlus } from 'lucide-vue-next'

const props = defineProps({
  mapData: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['open-target', 'add-evidence', 'add-timeline', 'edit-location', 'map-unmapped', 'move-marker', 'create-node'])

const sourceFilter = ref('all')
const statusFilter = ref('all')
const typeFilter = ref('all')
const selectedMarkerId = ref(null)
const mapEl = ref(null)
const mapboxError = ref('')
const createMode = ref(null)

const mapboxToken = import.meta.env.VITE_MAPBOX_TOKEN || ''
const mapboxTokenConfigured = Boolean(mapboxToken)
let mapInstance = null
let mapboxMarkers = []
let mapboxgl = null
let mapboxLoadPromise = null
let ensureFrame = 0
let retryTimer = 0
let resizeObserver = null
const markers = computed(() => props.mapData?.markers ?? [])
const unmapped = computed(() => props.mapData?.unmapped ?? [])
const warnings = computed(() => props.mapData?.warnings ?? [])
const shouldUseMapbox = computed(() => mapboxTokenConfigured && !mapboxError.value)

const sourceOptions = computed(() => ['all', ...new Set(markers.value.map(m => m.source_type).filter(Boolean))])
const statusOptions = computed(() => ['all', ...new Set(markers.value.map(m => m.verification_status).filter(Boolean))])
const typeOptions = computed(() => ['all', ...new Set(markers.value.map(m => m.entity_type).filter(Boolean))])

function logMapbox(message, data = undefined) {
  if (data === undefined) {
    console.info(`[OSIF Mapbox] ${message}`)
  } else {
    console.info(`[OSIF Mapbox] ${message}`, data)
  }
}

const filteredMarkers = computed(() => {
  return markers.value.filter(marker => {
    if (sourceFilter.value !== 'all' && marker.source_type !== sourceFilter.value) return false
    if (statusFilter.value !== 'all' && marker.verification_status !== statusFilter.value) return false
    if (typeFilter.value !== 'all' && marker.entity_type !== typeFilter.value) return false
    return true
  })
})

const selectedMarker = computed(() => {
  return filteredMarkers.value.find(marker => marker.id === selectedMarkerId.value) || filteredMarkers.value[0] || null
})

const bounds = computed(() => {
  if (!filteredMarkers.value.length) return null
  const lats = filteredMarkers.value.map(marker => marker.latitude)
  const lons = filteredMarkers.value.map(marker => marker.longitude)
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  }
})

const pathMarkers = computed(() => {
  return filteredMarkers.value
    .filter(marker => marker.occurred_at)
    .sort((a, b) => new Date(a.occurred_at) - new Date(b.occurred_at))
})

const pathPoints = computed(() => pathMarkers.value.map(marker => position(marker)).join(' '))

const createModeLabel = computed(() => {
  if (createMode.value === 'person') return 'Person'
  if (createMode.value === 'office') return 'Office'
  return 'Location'
})

function selectMarker(marker) {
  selectedMarkerId.value = marker.id
}

function markerElement(marker) {
  const el = document.createElement('button')
  el.type = 'button'
  el.className = `mapbox-marker-button ${marker.marker_type === 'evidence' ? 'is-evidence' : marker.marker_type === 'timeline_event' ? 'is-timeline' : marker.source_type === 'scan' ? 'is-scan' : 'is-manual'}`
  el.title = marker.label
  el.setAttribute('aria-label', marker.label)
  el.addEventListener('click', () => selectMarker(marker))
  return el
}

function canEditMarkerLocation(marker) {
  return marker?.target_type === 'entity' && marker?.source_type === 'manual'
}

function mapCenterDraft() {
  if (mapInstance) {
    const center = mapInstance.getCenter()
    return {
      latitude: Number(center.lat.toFixed(6)),
      longitude: Number(center.lng.toFixed(6)),
    }
  }
  if (selectedMarker.value) {
    return {
      latitude: selectedMarker.value.latitude,
      longitude: selectedMarker.value.longitude,
    }
  }
  const b = bounds.value
  if (b) {
    return {
      latitude: Number(((b.minLat + b.maxLat) / 2).toFixed(6)),
      longitude: Number(((b.minLon + b.maxLon) / 2).toFixed(6)),
    }
  }
  return { latitude: '', longitude: '' }
}

function defaultNodeLabel(type) {
  if (type === 'person') return 'Person'
  if (type === 'office') return 'Office'
  return 'Location'
}

function createNodeFromMap(type, coords = mapCenterDraft()) {
  emit('create-node', {
    type,
    label: '',
    value: '',
    address_text: defaultNodeLabel(type),
    latitude: coords.latitude,
    longitude: coords.longitude,
    location_precision: coords.latitude === '' || coords.longitude === '' ? 'unknown' : 'exact',
  })
  createMode.value = null
}

function beginCreateNode(type) {
  createMode.value = type
  logMapbox('create node mode started', { type })
}

function cancelCreateMode() {
  createMode.value = null
}

function clearMapboxMarkers() {
  for (const marker of mapboxMarkers) marker.remove()
  mapboxMarkers = []
}

async function loadMapbox() {
  if (!mapboxgl) {
    if (!mapboxLoadPromise) {
      logMapbox('loading mapbox-gl package')
      mapboxLoadPromise = Promise.all([
        import('mapbox-gl/dist/mapbox-gl.css'),
        import('mapbox-gl'),
      ]).then(([, mod]) => {
        mapboxgl = mod.default
        logMapbox('mapbox-gl package loaded', { version: mapboxgl.version || 'unknown' })
        return mapboxgl
      }).catch((error) => {
        mapboxLoadPromise = null
        throw error
      })
    }
    await mapboxLoadPromise
  }
  return mapboxgl
}

function getContainerRect() {
  if (!mapEl.value) return { width: 0, height: 0 }
  const rect = mapEl.value.getBoundingClientRect()
  return {
    width: Math.round(rect.width),
    height: Math.round(rect.height),
  }
}

function hasVisibleMapContainer(rect = getContainerRect()) {
  return rect.width > 0 && rect.height > 0
}

function scheduleRetry() {
  if (retryTimer) return
  retryTimer = window.setTimeout(() => {
    retryTimer = 0
    scheduleEnsureMapbox()
  }, 100)
}

function scheduleEnsureMapbox() {
  if (ensureFrame) cancelAnimationFrame(ensureFrame)
  ensureFrame = requestAnimationFrame(() => {
    ensureFrame = 0
    ensureMapbox()
  })
}

function attachResizeObserver() {
  if (!mapEl.value || resizeObserver) return
  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    const width = Math.round(entry?.contentRect?.width || 0)
    const height = Math.round(entry?.contentRect?.height || 0)
    logMapbox('container resize observed', { width, height })
    if (!width || !height) return
    mapInstance?.resize()
    syncMapboxMarkers()
  })
  resizeObserver.observe(mapEl.value)
}

function syncMapboxMarkers() {
  if (!mapInstance || !shouldUseMapbox.value || !mapboxgl) {
    logMapbox('sync skipped', {
      hasMap: Boolean(mapInstance),
      shouldUseMapbox: shouldUseMapbox.value,
      hasMapbox: Boolean(mapboxgl),
    })
    return
  }
  const rect = getContainerRect()
  if (!hasVisibleMapContainer(rect)) {
    logMapbox('sync deferred: container not visible', rect)
    scheduleRetry()
    return
  }
  mapInstance.resize()
  clearMapboxMarkers()
  logMapbox('syncing markers', { count: filteredMarkers.value.length })
  for (const marker of filteredMarkers.value) {
    const mapMarker = new mapboxgl.Marker({
      element: markerElement(marker),
      anchor: 'center',
      draggable: canEditMarkerLocation(marker),
    })
      .setLngLat([marker.longitude, marker.latitude])
      .addTo(mapInstance)

    if (canEditMarkerLocation(marker)) {
      mapMarker.on('dragend', () => {
        const lngLat = mapMarker.getLngLat()
        emit('move-marker', {
          marker,
          latitude: Number(lngLat.lat.toFixed(6)),
          longitude: Number(lngLat.lng.toFixed(6)),
        })
      })
    }

    mapboxMarkers.push(mapMarker)
  }
  if (filteredMarkers.value.length) {
    const b = bounds.value
    if (filteredMarkers.value.length === 1) {
      const marker = filteredMarkers.value[0]
      logMapbox('jumping to single marker', {
        label: marker.label,
        longitude: marker.longitude,
        latitude: marker.latitude,
      })
      mapInstance.jumpTo({
        center: [marker.longitude, marker.latitude],
        zoom: 10,
      })
    } else if (b) {
      logMapbox('fitting bounds', b)
      mapInstance.fitBounds(
        [[b.minLon, b.minLat], [b.maxLon, b.maxLat]],
        { padding: 72, maxZoom: 13, duration: 0 }
      )
    }
  }
}

async function ensureMapbox() {
  if (!shouldUseMapbox.value || !mapEl.value) {
    logMapbox('initialization skipped', {
      tokenConfigured: mapboxTokenConfigured,
      mapboxError: mapboxError.value || null,
      hasContainer: Boolean(mapEl.value),
    })
    return
  }
  await nextTick()
  try {
    const mapbox = await loadMapbox()
    mapbox.accessToken = mapboxToken
    attachResizeObserver()
    const rect = getContainerRect()
    logMapbox('initializing map', {
      tokenConfigured: mapboxTokenConfigured,
      containerWidth: rect.width,
      containerHeight: rect.height,
      markers: filteredMarkers.value.length,
      bounds: props.mapData?.bounds || null,
    })
    if (!hasVisibleMapContainer(rect)) {
      logMapbox('initialization deferred: container not visible', rect)
      scheduleRetry()
      return
    }
    if (!mapInstance) {
      const center = props.mapData?.bounds
        ? [props.mapData.bounds.center_longitude, props.mapData.bounds.center_latitude]
        : [0, 20]
      mapInstance = new mapbox.Map({
        container: mapEl.value,
        style: 'mapbox://styles/mapbox/dark-v11',
        center,
        zoom: props.mapData?.bounds ? 4 : 1.5,
        attributionControl: false,
      })
      window.__osifCaseMapbox = mapInstance
      logMapbox('map instance created', { center, zoom: props.mapData?.bounds ? 4 : 1.5 })
      mapInstance.addControl(new mapbox.NavigationControl({ visualizePitch: true }), 'top-right')
      mapInstance.on('error', (event) => {
        console.error('[OSIF Mapbox] mapbox error', event?.error || event)
        mapboxError.value = event?.error?.message || 'Mapbox rendering failed.'
      })
      mapInstance.on('load', () => {
        logMapbox('map load event', {
          loaded: mapInstance.loaded(),
          styleLoaded: mapInstance.isStyleLoaded(),
        })
        mapInstance.resize()
        syncMapboxMarkers()
      })
      mapInstance.on('idle', () => {
        const canvas = mapInstance.getCanvas()
        logMapbox('map idle event', {
          loaded: mapInstance.loaded(),
          styleLoaded: mapInstance.isStyleLoaded(),
          canvasWidth: canvas.width,
          canvasHeight: canvas.height,
          markerCount: mapboxMarkers.length,
        })
      })
      mapInstance.on('click', (event) => {
        if (!createMode.value) return
        createNodeFromMap(createMode.value, {
          latitude: Number(event.lngLat.lat.toFixed(6)),
          longitude: Number(event.lngLat.lng.toFixed(6)),
        })
      })
      requestAnimationFrame(() => {
        const nextRect = getContainerRect()
        logMapbox('post-frame resize', {
          containerWidth: nextRect.width,
          containerHeight: nextRect.height,
        })
        if (!hasVisibleMapContainer(nextRect)) {
          scheduleRetry()
          return
        }
        mapInstance?.resize()
        syncMapboxMarkers()
      })
      return
    }
    requestAnimationFrame(() => {
      const rect = getContainerRect()
      logMapbox('resizing existing map', {
        containerWidth: rect.width,
        containerHeight: rect.height,
      })
      if (!hasVisibleMapContainer(rect)) {
        scheduleRetry()
        return
      }
      mapInstance?.resize()
      syncMapboxMarkers()
    })
  } catch (error) {
    console.error('[OSIF Mapbox] initialization failed', error)
    mapboxError.value = error?.message || 'Mapbox failed to initialize.'
  }
}

function position(marker) {
  const b = bounds.value
  if (!b) return '50,50'
  const lonRange = b.maxLon - b.minLon
  const latRange = b.maxLat - b.minLat
  const x = lonRange === 0 ? 50 : 8 + ((marker.longitude - b.minLon) / lonRange) * 84
  const y = latRange === 0 ? 50 : 8 + (1 - ((marker.latitude - b.minLat) / latRange)) * 84
  return `${x},${y}`
}

function pointStyle(marker) {
  const [x, y] = position(marker).split(',')
  return { left: `${x}%`, top: `${y}%` }
}

function markerClass(marker) {
  if (marker.marker_type === 'evidence') return 'border-cyan-300 bg-cyan-400 text-cyan-950'
  if (marker.marker_type === 'timeline_event') return 'border-emerald-300 bg-emerald-400 text-emerald-950'
  if (marker.source_type === 'scan') return 'border-amber-300 bg-amber-400 text-amber-950'
  if (marker.verification_status === 'confirmed') return 'border-blue-300 bg-blue-400 text-blue-950'
  if (marker.verification_status === 'rejected') return 'border-red-300 bg-red-400 text-red-950'
  return 'border-fuchsia-300 bg-fuchsia-400 text-fuchsia-950'
}

function markerIcon(marker) {
  if (marker.marker_type === 'evidence') return FileImage
  if (marker.marker_type === 'timeline_event') return Route
  if (marker.source_type === 'scan') return Crosshair
  if (marker.verification_status === 'confirmed') return ShieldCheck
  return MapPin
}

function fmtCoord(value) {
  return Number(value).toFixed(5)
}

function fmtDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  logMapbox('component mounted', { tokenConfigured: mapboxTokenConfigured })
  scheduleEnsureMapbox()
})

watch(filteredMarkers, () => {
  logMapbox('filtered markers changed', { count: filteredMarkers.value.length })
  scheduleEnsureMapbox()
})

watch(() => props.mapData, () => {
  logMapbox('map data changed', {
    markers: props.mapData?.markers?.length || 0,
    unmapped: props.mapData?.unmapped?.length || 0,
  })
  scheduleEnsureMapbox()
})

onBeforeUnmount(() => {
  if (ensureFrame) cancelAnimationFrame(ensureFrame)
  if (retryTimer) window.clearTimeout(retryTimer)
  resizeObserver?.disconnect()
  resizeObserver = null
  clearMapboxMarkers()
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<template>
  <div class="h-full min-h-0 grid grid-cols-[280px_minmax(0,1fr)_340px] overflow-hidden" style="background-color: var(--bg-primary)">
    <aside class="border-r overflow-y-auto" style="border-color: var(--border); background-color: var(--bg-secondary)">
      <div class="p-4 border-b" style="border-color: var(--border)">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h2 class="text-sm font-semibold" style="color: var(--text-primary)">Case Map</h2>
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ filteredMarkers.length }} plotted · {{ unmapped.length }} unmapped</p>
          </div>
          <span class="badge" :class="shouldUseMapbox ? 'badge-green' : 'badge-amber'">
            {{ shouldUseMapbox ? 'Mapbox ready' : 'Static map' }}
          </span>
        </div>

      <div class="mt-4 space-y-2">
          <select v-model="sourceFilter" class="input text-xs">
            <option v-for="option in sourceOptions" :key="option" :value="option">Source: {{ option.replace(/_/g, ' ') }}</option>
          </select>
          <select v-model="statusFilter" class="input text-xs">
            <option v-for="option in statusOptions" :key="option" :value="option">Status: {{ option.replace(/_/g, ' ') }}</option>
          </select>
          <select v-model="typeFilter" class="input text-xs">
            <option v-for="option in typeOptions" :key="option" :value="option">Type: {{ option.replace(/_/g, ' ') }}</option>
          </select>
        </div>

        <div class="mt-4 pt-4 border-t" style="border-color: var(--border)">
          <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color: var(--text-muted)">Add From Map</p>
          <div class="grid grid-cols-3 gap-2">
            <button class="btn-secondary text-[10px] px-2 py-2 flex flex-col items-center gap-1" @click="beginCreateNode('person')">
              <UserPlus class="h-3.5 w-3.5" />
              Person
            </button>
            <button class="btn-secondary text-[10px] px-2 py-2 flex flex-col items-center gap-1" @click="beginCreateNode('location')">
              <MapPin class="h-3.5 w-3.5" />
              Location
            </button>
            <button class="btn-secondary text-[10px] px-2 py-2 flex flex-col items-center gap-1" @click="beginCreateNode('office')">
              <Building2 class="h-3.5 w-3.5" />
              Office
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="p-4 text-sm" style="color: var(--text-muted)">Loading map data…</div>
      <div v-else-if="filteredMarkers.length === 0" class="p-4 text-sm" style="color: var(--text-muted)">No plotted locations match the filters.</div>
      <div v-else class="p-3 space-y-2">
        <button
          v-for="marker in filteredMarkers"
          :key="marker.id"
          type="button"
          class="w-full text-left rounded-lg border p-3 transition-all"
          :class="selectedMarker?.id === marker.id ? 'border-blue-400' : 'hover:border-slate-500'"
          style="background-color: var(--bg-primary); border-color: var(--border)"
          @click="selectMarker(marker)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="text-sm font-medium truncate" style="color: var(--text-primary)" :title="marker.label">{{ marker.label }}</p>
              <p class="text-xs mt-0.5 truncate" style="color: var(--text-muted)" :title="marker.address_text">{{ marker.address_text || marker.entity_type }}</p>
            </div>
            <component :is="markerIcon(marker)" class="h-4 w-4 shrink-0" style="color: var(--text-muted)" />
          </div>
          <div class="flex flex-wrap gap-1.5 mt-2">
            <span class="badge badge-slate">{{ marker.source_type }}</span>
            <span class="badge" :class="marker.approximate ? 'badge-amber' : 'badge-green'">{{ marker.precision }}</span>
          </div>
        </button>
      </div>
    </aside>

    <main class="relative min-h-0 overflow-hidden">
      <div v-if="shouldUseMapbox" ref="mapEl" class="absolute inset-0 h-full w-full"></div>
      <div v-else class="absolute inset-0 case-map-grid"></div>
      <svg v-if="!shouldUseMapbox" class="absolute inset-0 h-full w-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline
          v-if="pathMarkers.length > 1"
          :points="pathPoints"
          fill="none"
          stroke="rgba(16, 185, 129, 0.75)"
          stroke-width="0.55"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      <div class="absolute top-4 left-4 z-10 flex flex-wrap gap-2">
        <span class="badge badge-slate">Markers {{ filteredMarkers.length }}</span>
        <span v-if="pathMarkers.length > 1" class="badge badge-green">Movement path {{ pathMarkers.length }}</span>
        <span v-if="warnings.length" class="badge badge-amber">Approximate geolocation</span>
        <span v-if="mapboxError" class="badge badge-red" :title="mapboxError">Mapbox fallback</span>
      </div>

      <div v-if="createMode" class="absolute top-4 right-4 z-20 w-72 rounded-lg border p-3 shadow-xl" style="border-color: var(--border); background-color: var(--bg-secondary)">
        <div class="flex items-start gap-2">
          <LocateFixed class="h-4 w-4 shrink-0 mt-0.5" style="color: var(--text-muted)" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium" style="color: var(--text-primary)">Place {{ createModeLabel }}</p>
            <p class="text-xs mt-1" style="color: var(--text-muted)">Click the map to use that point, or use the current center.</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-3">
          <button class="btn-secondary text-xs" @click="createNodeFromMap(createMode)">Use Center</button>
          <button class="btn-secondary text-xs" @click="cancelCreateMode">Cancel</button>
        </div>
      </div>

      <button
        v-if="!shouldUseMapbox"
        v-for="marker in filteredMarkers"
        :key="marker.id"
        type="button"
        class="absolute z-20 h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 shadow-lg flex items-center justify-center transition-transform hover:scale-110"
        :class="[markerClass(marker), selectedMarker?.id === marker.id ? 'ring-4 ring-white/25' : '']"
        :style="pointStyle(marker)"
        :title="marker.label"
        @click="selectMarker(marker)"
      >
        <component :is="markerIcon(marker)" class="h-4 w-4" />
      </button>

      <div v-if="filteredMarkers.length === 0 && !loading" class="absolute inset-0 flex items-center justify-center">
        <div class="text-center">
          <Search class="h-10 w-10 mx-auto mb-3" style="color: var(--text-muted)" />
          <p class="text-sm" style="color: var(--text-muted)">No map markers available.</p>
        </div>
      </div>
    </main>

    <aside class="border-l overflow-y-auto" style="border-color: var(--border); background-color: var(--bg-secondary)">
      <div v-if="selectedMarker" class="p-4 space-y-4">
        <div>
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h3 class="text-base font-semibold break-words" style="color: var(--text-primary)">{{ selectedMarker.label }}</h3>
              <p class="text-xs mt-1" style="color: var(--text-muted)">
                {{ fmtCoord(selectedMarker.latitude) }}, {{ fmtCoord(selectedMarker.longitude) }}
              </p>
            </div>
            <component :is="markerIcon(selectedMarker)" class="h-5 w-5 shrink-0" style="color: var(--text-muted)" />
          </div>
          <p v-if="selectedMarker.description" class="text-sm mt-3" style="color: var(--text-secondary)">{{ selectedMarker.description }}</p>
        </div>

        <div class="flex flex-wrap gap-1.5">
          <span class="badge badge-blue">{{ selectedMarker.entity_type }}</span>
          <span class="badge badge-slate">{{ selectedMarker.source_type }}</span>
          <span class="badge" :class="selectedMarker.approximate ? 'badge-amber' : 'badge-green'">{{ selectedMarker.precision }}</span>
          <span class="badge badge-slate">{{ selectedMarker.verification_status }}</span>
        </div>

        <div v-if="selectedMarker.approximate" class="rounded-lg border p-3 flex gap-2" style="border-color: rgba(245, 158, 11, 0.35); background-color: rgba(245, 158, 11, 0.08)">
          <AlertTriangle class="h-4 w-4 shrink-0 text-amber-300" />
          <p class="text-xs text-amber-200">Approximate marker. Verify with direct evidence before treating this as physical presence.</p>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
          <div class="rounded-lg border p-3" style="border-color: var(--border); background-color: var(--bg-primary)">
            <p style="color: var(--text-muted)">Confidence</p>
            <p class="font-mono mt-1" style="color: var(--text-primary)">{{ selectedMarker.confidence == null ? 'unknown' : Math.round(selectedMarker.confidence * 100) + '%' }}</p>
          </div>
          <div class="rounded-lg border p-3" style="border-color: var(--border); background-color: var(--bg-primary)">
            <p style="color: var(--text-muted)">Observed</p>
            <p class="font-mono mt-1" style="color: var(--text-primary)">{{ fmtDate(selectedMarker.occurred_at || selectedMarker.created_at) || 'unknown' }}</p>
          </div>
        </div>

        <div v-if="selectedMarker.links?.length">
          <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color: var(--text-muted)">Links</p>
          <div class="space-y-2">
            <button
              v-for="link in selectedMarker.links"
              :key="`${link.target_type}:${link.target_id}`"
              type="button"
              class="w-full text-left rounded-lg border p-2.5"
              style="border-color: var(--border); background-color: var(--bg-primary)"
              @click="emit('open-target', link)"
            >
              <span class="badge badge-slate mr-2">{{ link.target_type }}</span>
              <span class="text-xs" style="color: var(--text-secondary)">{{ link.label || link.target_id }}</span>
            </button>
          </div>
        </div>

        <div class="flex gap-2">
          <button class="btn-secondary text-xs flex-1" @click="emit('add-evidence', selectedMarker)">Attach Evidence</button>
          <button class="btn-secondary text-xs flex-1" @click="emit('add-timeline', selectedMarker)">Timeline</button>
        </div>

        <button
          v-if="canEditMarkerLocation(selectedMarker)"
          class="btn-secondary text-xs w-full"
          @click="emit('edit-location', selectedMarker)"
        >
          Edit Location
        </button>

        <div v-if="warnings.length" class="space-y-2">
          <p class="text-xs font-semibold uppercase tracking-wider" style="color: var(--text-muted)">Warnings</p>
          <div v-for="warning in warnings" :key="warning" class="text-xs rounded-lg border p-2.5 text-amber-200" style="border-color: rgba(245, 158, 11, 0.35); background-color: rgba(245, 158, 11, 0.08)">
            {{ warning }}
          </div>
        </div>

        <div v-if="unmapped.length">
          <p class="text-xs font-semibold uppercase tracking-wider mb-2" style="color: var(--text-muted)">Unmapped</p>
          <div class="space-y-2">
            <div v-for="item in unmapped.slice(0, 6)" :key="`${item.target_type}:${item.target_id}`" class="rounded-lg border p-2.5" style="border-color: var(--border); background-color: var(--bg-primary)">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="text-xs font-medium truncate" style="color: var(--text-primary)" :title="item.label">{{ item.label }}</p>
                  <p class="text-[10px] mt-0.5" style="color: var(--text-muted)">{{ item.entity_type }} · {{ item.reason.replace(/_/g, ' ') }}</p>
                </div>
                <button
                  v-if="item.target_type === 'entity' && item.source_type === 'manual'"
                  class="btn-secondary text-[10px] px-2 py-1"
                  @click="emit('map-unmapped', item)"
                >
                  Map
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="p-4 text-sm" style="color: var(--text-muted)">Select a marker.</div>
    </aside>
  </div>
</template>

<style scoped>
.case-map-grid {
  background:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    #08111f;
  background-size: 42px 42px, 42px 42px, 100% 100%;
}

:deep(.mapbox-marker-button) {
  width: 26px;
  height: 26px;
  border-radius: 9999px;
  border: 2px solid rgba(255, 255, 255, 0.82);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.35);
  cursor: pointer;
}

:deep(.mapbox-marker-button.is-manual) {
  background: #60a5fa;
}

:deep(.mapbox-marker-button.is-scan) {
  background: #f59e0b;
}

:deep(.mapbox-marker-button.is-evidence) {
  background: #22d3ee;
}

:deep(.mapbox-marker-button.is-timeline) {
  background: #34d399;
}
</style>
