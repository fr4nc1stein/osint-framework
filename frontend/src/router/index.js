import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ScanView from '../views/ScanView.vue'
import ScansListView from '../views/ScansListView.vue'
import Templates from '../views/Templates.vue'
import CasesList from '../views/CasesList.vue'
import CaseDetail from '../views/CaseDetail.vue'
import ReportsView from '../views/ReportsView.vue'
import IntegrationsView from '../views/IntegrationsView.vue'
import AiAnalystView from '../views/AiAnalystView.vue'
import AiSettingsView from '../views/AiSettingsView.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/scans', name: 'ScansListView', component: ScansListView },
  { path: '/scan/:id', name: 'ScanView', component: ScanView },
  { path: '/templates', name: 'Templates', component: Templates },
  { path: '/cases', name: 'CasesList', component: CasesList },
  { path: '/cases/:id', name: 'CaseDetail', component: CaseDetail },
  { path: '/reports', name: 'Reports', component: ReportsView },
  { path: '/integrations', name: 'Integrations', component: IntegrationsView },
  { path: '/ai', name: 'AiAnalyst', component: AiAnalystView },
  { path: '/settings/ai', name: 'AiSettings', component: AiSettingsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
