<script setup>
import { onMounted } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
onMounted(() => themeStore.init())
</script>

<template>
  <div class="flex h-screen overflow-hidden" style="background-color: var(--bg-primary)">
    <AppSidebar />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
