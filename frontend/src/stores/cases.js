import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useCasesStore = defineStore('cases', {
  state: () => ({
    cases: [],
    currentCase: null,
    caseScans: [],
    caseGraph: null,
    caseNotes: [],
    caseReports: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchCases() {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.getCases()
        this.cases = data
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },

    async fetchCase(id) {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.getCase(id)
        this.currentCase = data
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      } finally {
        this.loading = false
      }
    },

    async createCase(payload) {
      const { data } = await api.createCase(payload)
      this.cases.unshift(data)
      return data
    },

    async updateCase(id, payload) {
      const { data } = await api.updateCase(id, payload)
      this.currentCase = data
      const idx = this.cases.findIndex((c) => c.id === id)
      if (idx !== -1) this.cases[idx] = data
      return data
    },

    async deleteCase(id) {
      await api.deleteCase(id)
      this.cases = this.cases.filter((c) => c.id !== id)
    },

    async fetchCaseScans(caseId) {
      const { data } = await api.getCaseScans(caseId)
      this.caseScans = data
      return data
    },

    async fetchCaseGraph(caseId) {
      const { data } = await api.getCaseGraph(caseId)
      this.caseGraph = data
      return data
    },

    async fetchCaseNotes(caseId) {
      const { data } = await api.getCaseNotes(caseId)
      this.caseNotes = data
      return data
    },

    async createNote(caseId, payload) {
      const { data } = await api.createNote(caseId, payload)
      this.caseNotes.unshift(data)
      return data
    },

    async deleteNote(caseId, noteId) {
      await api.deleteNote(caseId, noteId)
      this.caseNotes = this.caseNotes.filter((n) => n.id !== noteId)
    },

    async fetchCaseReports(caseId) {
      const { data } = await api.getCaseReports(caseId)
      this.caseReports = data
      return data
    },

    async createReport(caseId, payload) {
      const { data } = await api.createReport(caseId, payload)
      this.caseReports.unshift(data)
      return data
    },

    async deleteReport(reportId) {
      await api.deleteReport(reportId)
      this.caseReports = this.caseReports.filter((r) => r.id !== reportId)
    },
  },
})
