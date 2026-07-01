<script setup>
import AppSidebar from './components/AppSidebar.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-slate-950">
    <AppSidebar />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
