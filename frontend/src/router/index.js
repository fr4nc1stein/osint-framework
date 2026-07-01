import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import ScanView from '../views/ScanView.vue';
import Templates from '../views/Templates.vue';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/scan/:id',
    name: 'ScanView',
    component: ScanView,
  },
  {
    path: '/templates',
    name: 'Templates',
    component: Templates,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
