<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  {
    name: 'Dashboard',
    to: '/',
    icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  },
  {
    name: 'Templates',
    to: '/templates',
    icon: '<path d="M8 2h8l4 4v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M16 2v5h5"/><path d="M10 13h6M10 17h4"/>',
  },
]

function isActive(item) {
  if (item.to === '/' && route.path === '/') return true
  if (item.to !== '/' && route.path.startsWith(item.to)) return true
  return false
}
</script>

<template>
  <aside class="flex w-20 shrink-0 flex-col border-r border-slate-800 bg-[#0b1120]">
    <div class="flex h-16 items-center justify-center border-b border-slate-800">
      <div class="flex h-9 w-9 items-center justify-center rounded-md border border-blue-500/40 bg-blue-500/10">
        <svg class="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.7">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <nav class="flex flex-1 flex-col items-center gap-1 overflow-y-auto p-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="item.to"
        class="nav-icon-btn"
        :class="isActive(item) ? 'nav-icon-btn--active' : ''"
        :title="item.name"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" v-html="item.icon" />
        <span class="mt-1 max-w-[64px] truncate text-[9px] leading-none">{{ item.name }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped>
.nav-icon-btn {
  @apply flex h-12 w-16 flex-col items-center justify-center rounded-md border border-transparent text-slate-500
         transition-all duration-150 hover:bg-slate-800/80 hover:text-slate-100;
}
.nav-icon-btn--active {
  @apply border-blue-500/30 bg-blue-500/10 text-blue-300;
}
</style>
