import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: localStorage.getItem('osif-theme') || 'dark',
  }),
  actions: {
    init() {
      document.documentElement.setAttribute('data-theme', this.theme)
    },
    toggle() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('osif-theme', this.theme)
      document.documentElement.setAttribute('data-theme', this.theme)
    },
    setTheme(t) {
      this.theme = t
      localStorage.setItem('osif-theme', t)
      document.documentElement.setAttribute('data-theme', t)
    },
  },
})
