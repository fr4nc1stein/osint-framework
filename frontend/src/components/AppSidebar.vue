<script setup>
import { useRoute } from 'vue-router'
import { useThemeStore } from '../stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

const navItems = [
  {
    name: 'Dashboard',
    to: '/',
    exact: true,
    icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  },
  {
    name: 'Cases',
    to: '/cases',
    icon: '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
  },
  {
    name: 'Scans',
    to: '/scans',
    icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6M8 11h6"/>',
  },
  {
    name: 'Reports',
    to: '/reports',
    icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
  },
  {
    name: 'Templates',
    to: '/templates',
    icon: '<path d="M8 2h8l4 4v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M16 2v5h5"/><path d="M10 13h6M10 17h4"/>',
  },
  {
    name: 'Integrations',
    to: '/integrations',
    icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  },
  {
    name: 'AI Analyst',
    to: '/ai',
    icon: '<path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 8v4l3 3"/><circle cx="18" cy="5" r="3"/>',
  },
  {
    name: 'AI Settings',
    to: '/settings/ai',
    icon: '<circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>',
  },
]

function isActive(item) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}
</script>

<template>
  <aside class="flex w-20 shrink-0 flex-col border-r" style="background-color: var(--bg-sidebar); border-color: var(--border)">
    <!-- Logo -->
    <div class="flex h-16 items-center justify-center border-b" style="border-color: var(--border)">
      <div class="flex h-9 w-9 items-center justify-center rounded-md border border-blue-500/40 bg-blue-500/10">
        <svg class="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.7">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Nav links -->
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

    <!-- Theme toggle -->
    <div class="flex items-center justify-center p-3 border-t" style="border-color: var(--border)">
      <button
        class="flex h-10 w-10 flex-col items-center justify-center rounded-md transition-all duration-150"
        style="color: var(--text-secondary)"
        :title="themeStore.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
        @click="themeStore.toggle()"
      >
        <!-- Sun icon (shown in dark mode) -->
        <svg v-if="themeStore.theme === 'dark'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <!-- Moon icon (shown in light mode) -->
        <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.nav-icon-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 3rem;
  width: 4rem;
  border-radius: 0.375rem;
  border: 1px solid transparent;
  color: var(--text-muted);
  transition: all 0.15s;
}
.nav-icon-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}
.nav-icon-btn--active {
  border-color: rgba(59,130,246,0.3);
  background-color: rgba(59,130,246,0.1);
  color: #93c5fd;
}
</style>
