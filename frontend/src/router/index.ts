/**
 * Application router configuration.
 *
 * Defines all top-level routes for Legatio AI. Routes are
 * lazy-loaded to optimize initial bundle size.
 *
 * Reference: 02-ARCHITECTURE.md Section 6.1
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/HomePage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/pages/RegisterPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/constitutions',
    name: 'constitutions',
    component: () => import('@/pages/ConstitutionsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/negotiations',
    name: 'negotiations',
    component: () => import('@/pages/NegotiationsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/approvals',
    name: 'approvals',
    component: () => import('@/pages/ApprovalsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/audit',
    name: 'audit',
    component: () => import('@/pages/AuditPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFoundPage.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
