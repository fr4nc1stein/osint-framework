import { defineStore } from 'pinia';
import { api } from '../api/client';

export const useModulesStore = defineStore('modules', {
  state: () => ({
    modules: [],
    loading: false,
    error: null,
  }),

  getters: {
    modulesByCategory: (state) => {
      const grouped = {};
      state.modules.forEach(module => {
        if (!grouped[module.category]) {
          grouped[module.category] = [];
        }
        grouped[module.category].push(module);
      });
      return grouped;
    },
  },

  actions: {
    async fetchModules() {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.getModules();
        this.modules = response.data;
      } catch (error) {
        this.error = error.message;
        console.error('Failed to fetch modules:', error);
      } finally {
        this.loading = false;
      }
    },
  },
});
