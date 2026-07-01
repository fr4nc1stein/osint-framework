import { defineStore } from 'pinia';
import { api } from '../api/client';

export const useScansStore = defineStore('scans', {
  state: () => ({
    scans: [],
    currentScan: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchScans() {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.getScans();
        this.scans = response.data;
      } catch (error) {
        this.error = error.message;
        console.error('Failed to fetch scans:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchScan(id) {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.getScan(id);
        this.currentScan = response.data;
      } catch (error) {
        this.error = error.message;
        console.error('Failed to fetch scan:', error);
      } finally {
        this.loading = false;
      }
    },

    async createScan(scanData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.createScan(scanData);
        this.scans.unshift(response.data);
        return response.data;
      } catch (error) {
        this.error = error.message;
        console.error('Failed to create scan:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    updateScanFromWebSocket(scanData) {
      const index = this.scans.findIndex(s => s.id === scanData.id);
      if (index !== -1) {
        this.scans[index] = { ...this.scans[index], ...scanData };
      }
      if (this.currentScan?.id === scanData.id) {
        this.currentScan = { ...this.currentScan, ...scanData };
      }
    },
  },
});
