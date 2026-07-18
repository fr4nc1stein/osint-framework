import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useCasesStore = defineStore('cases', {
  state: () => ({
    cases: [],
    currentCase: null,
    currentCaseId: null,
    caseScans: [],
    caseScansCaseId: null,
    caseGraph: null,
    caseGraphCaseId: null,
    caseMap: null,
    caseMapCaseId: null,
    caseGeolocations: [],
    caseGeolocationsCaseId: null,
    caseEntities: [],
    caseEntitiesCaseId: null,
    caseRelationships: [],
    caseRelationshipsCaseId: null,
    caseEvidence: [],
    caseEvidenceCaseId: null,
    caseTimelineEvents: [],
    caseTimelineEventsCaseId: null,
    caseLeads: null,
    caseLeadsCaseId: null,
    caseLeadsParams: null,
    caseNotes: [],
    caseNotesCaseId: null,
    caseReports: [],
    caseReportsCaseId: null,
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
        if (this.currentCaseId !== id) {
          this.currentCase = null
          this.caseScans = []
          this.caseScansCaseId = null
          this.caseGraph = null
          this.caseGraphCaseId = null
          this.caseMap = null
          this.caseMapCaseId = null
          this.caseGeolocations = []
          this.caseGeolocationsCaseId = null
          this.caseEntities = []
          this.caseEntitiesCaseId = null
          this.caseRelationships = []
          this.caseRelationshipsCaseId = null
          this.caseEvidence = []
          this.caseEvidenceCaseId = null
          this.caseTimelineEvents = []
          this.caseTimelineEventsCaseId = null
          this.caseLeads = null
          this.caseLeadsCaseId = null
          this.caseLeadsParams = null
          this.caseNotes = []
          this.caseNotesCaseId = null
          this.caseReports = []
          this.caseReportsCaseId = null
        }
        const { data } = await api.getCase(id)
        this.currentCase = data
        this.currentCaseId = id
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
      this.caseScansCaseId = caseId
      return data
    },

    async fetchCaseGraph(caseId) {
      const { data } = await api.getCaseGraph(caseId)
      this.caseGraph = data
      this.caseGraphCaseId = caseId
      return data
    },

    async fetchCaseMap(caseId) {
      const { data } = await api.getCaseMap(caseId)
      this.caseMap = data
      this.caseMapCaseId = caseId
      return data
    },

    async fetchCaseGeolocations(caseId, params = undefined) {
      const { data } = await api.getCaseGeolocations(caseId, params)
      if (!params?.target_type && !params?.target_id) {
        this.caseGeolocations = data
        this.caseGeolocationsCaseId = caseId
      }
      return data
    },

    async createCaseGeolocation(caseId, payload) {
      const { data } = await api.createCaseGeolocation(caseId, payload)
      this.caseGeolocations.unshift(data)
      this.caseMapCaseId = null
      await this.fetchCaseGraph(caseId)
      return data
    },

    async updateCaseGeolocation(caseId, geolocationId, payload) {
      const { data } = await api.updateCaseGeolocation(caseId, geolocationId, payload)
      const idx = this.caseGeolocations.findIndex(g => g.id === geolocationId)
      if (idx !== -1) this.caseGeolocations.splice(idx, 1, data)
      this.caseMapCaseId = null
      await this.fetchCaseGraph(caseId)
      return data
    },

    async deleteCaseGeolocation(caseId, geolocationId) {
      await api.deleteCaseGeolocation(caseId, geolocationId)
      this.caseGeolocations = this.caseGeolocations.filter(g => g.id !== geolocationId)
      this.caseMapCaseId = null
      await this.fetchCaseGraph(caseId)
    },

    async geocodeCaseAddress(caseId, payload) {
      const { data } = await api.geocodeCaseAddress(caseId, payload)
      return data
    },

    async fetchCaseEntities(caseId) {
      const { data } = await api.getCaseEntities(caseId)
      this.caseEntities = data
      this.caseEntitiesCaseId = caseId
      return data
    },

    async createCaseEntity(caseId, payload) {
      const { data } = await api.createCaseEntity(caseId, payload)
      this.caseEntities.unshift(data)
      await this.fetchCaseGraph(caseId)
      this.caseMapCaseId = null
      return data
    },

    async updateCaseEntity(caseId, entityId, payload) {
      const { data } = await api.updateCaseEntity(caseId, entityId, payload)
      const idx = this.caseEntities.findIndex(e => e.id === entityId)
      if (idx !== -1) this.caseEntities.splice(idx, 1, data)
      await this.fetchCaseGraph(caseId)
      this.caseMapCaseId = null
      return data
    },

    async deleteCaseEntity(caseId, entityId) {
      await api.deleteCaseEntity(caseId, entityId)
      this.caseEntities = this.caseEntities.filter(e => e.id !== entityId)
      await this.fetchCaseGraph(caseId)
      this.caseMapCaseId = null
    },

    async fetchCaseRelationships(caseId) {
      const { data } = await api.getCaseRelationships(caseId)
      this.caseRelationships = data
      this.caseRelationshipsCaseId = caseId
      return data
    },

    async createCaseRelationship(caseId, payload) {
      const { data } = await api.createCaseRelationship(caseId, payload)
      this.caseRelationships.unshift(data)
      await this.fetchCaseGraph(caseId)
      return data
    },

    async updateCaseRelationship(caseId, relationshipId, payload) {
      const { data } = await api.updateCaseRelationship(caseId, relationshipId, payload)
      const idx = this.caseRelationships.findIndex(r => r.id === relationshipId)
      if (idx !== -1) this.caseRelationships.splice(idx, 1, data)
      await this.fetchCaseGraph(caseId)
      return data
    },

    async deleteCaseRelationship(caseId, relationshipId) {
      await api.deleteCaseRelationship(caseId, relationshipId)
      this.caseRelationships = this.caseRelationships.filter(r => r.id !== relationshipId)
      await this.fetchCaseGraph(caseId)
    },

    async fetchCaseEvidence(caseId, params = undefined) {
      const { data } = await api.getCaseEvidence(caseId, params)
      if (!params?.target_type && !params?.target_id) {
        this.caseEvidence = data
        this.caseEvidenceCaseId = caseId
      }
      return data
    },

    async createCaseEvidence(caseId, payload) {
      const { data } = await api.createCaseEvidence(caseId, payload)
      this.caseEvidence.unshift(data)
      this.caseMapCaseId = null
      return data
    },

    async uploadCaseEvidence(caseId, formData) {
      const { data } = await api.uploadCaseEvidence(caseId, formData)
      this.caseEvidence.unshift(data)
      this.caseMapCaseId = null
      return data
    },

    async deleteCaseEvidence(caseId, evidenceId) {
      await api.deleteCaseEvidence(caseId, evidenceId)
      this.caseEvidence = this.caseEvidence.filter(e => e.id !== evidenceId)
      this.caseMapCaseId = null
    },

    async fetchCaseTimeline(caseId, params = undefined) {
      const { data } = await api.getCaseTimeline(caseId, params)
      if (!params?.target_type && !params?.target_id) {
        this.caseTimelineEvents = data
        this.caseTimelineEventsCaseId = caseId
      }
      return data
    },

    async createCaseTimelineEvent(caseId, payload) {
      const { data } = await api.createCaseTimelineEvent(caseId, payload)
      this.caseTimelineEvents.unshift(data)
      this.caseMapCaseId = null
      return data
    },

    async updateCaseTimelineEvent(caseId, eventId, payload) {
      const { data } = await api.updateCaseTimelineEvent(caseId, eventId, payload)
      const idx = this.caseTimelineEvents.findIndex(e => e.id === eventId)
      if (idx !== -1) this.caseTimelineEvents.splice(idx, 1, data)
      this.caseMapCaseId = null
      return data
    },

    async deleteCaseTimelineEvent(caseId, eventId) {
      await api.deleteCaseTimelineEvent(caseId, eventId)
      this.caseTimelineEvents = this.caseTimelineEvents.filter(e => e.id !== eventId)
      this.caseMapCaseId = null
    },

    async fetchCaseLeads(caseId, params = undefined) {
      const { data } = await api.getCaseLeads(caseId, params)
      this.caseLeads = data
      this.caseLeadsCaseId = caseId
      this.caseLeadsParams = params || {}
      return data
    },

    async reviewCaseLead(caseId, targetType, targetId, payload) {
      const { data } = await api.reviewCaseLead(caseId, targetType, targetId, payload)
      this.caseLeadsCaseId = null
      this.caseGraphCaseId = null
      this.caseMapCaseId = null
      return data
    },

    async fetchCaseNotes(caseId) {
      const { data } = await api.getCaseNotes(caseId)
      this.caseNotes = data
      this.caseNotesCaseId = caseId
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
      this.caseReportsCaseId = caseId
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
