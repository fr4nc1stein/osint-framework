<script setup>
import { onMounted } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import SetupBanner from './components/SetupBanner.vue'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
onMounted(() => themeStore.init())
</script>

<template>
  <div class="flex h-screen overflow-hidden" style="background-color: var(--bg-primary)">
    <AppSidebar />
    <div class="flex-1 flex flex-col overflow-hidden">
      <SetupBanner />
      <main class="flex-1 overflow-hidden">
        <router-view />
      </main>
    </div>
  </div>
</template>
