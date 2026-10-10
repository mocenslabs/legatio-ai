/**
 * FULL router replacement for frontend/src/router/index.ts
 * Adds: public Home, Help, Agents list/create
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { setupRouterGuards } from '@/router/guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/marketing/HomeView.vue'),
    meta: { public: true },
  },
  {
    path: '/help',
    name: 'help-public',
    component: () => import('@/views/help/HelpView.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/app',
    component: () => import('@/components/layout/AppShell.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.dashboard' },
      },
      {
        path: 'agents',
        name: 'agents',
        component: () => import('@/views/agents/AgentsListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.agents' },
      },
      {
        path: 'agents/new',
        name: 'agent-create',
        component: () => import('@/views/agents/AgentCreateView.vue'),
        meta: { requiresAuth: true, titleKey: 'agents.create' },
      },
      {
        path: 'constitutions',
        name: 'constitutions',
        component: () => import('@/views/constitutions/ConstitutionsListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.constitutions' },
      },
      {
        path: 'constitutions/new',
        name: 'constitution-create',
        component: () => import('@/views/constitutions/ConstitutionCreateView.vue'),
        meta: { requiresAuth: true, titleKey: 'constitutions.create' },
      },
      {
        path: 'constitutions/:id',
        name: 'constitution-detail',
        component: () => import('@/views/constitutions/ConstitutionDetailView.vue'),
        meta: { requiresAuth: true, titleKey: 'constitutions.detailTitle' },
      },
      {
        path: 'negotiations',
        name: 'negotiations',
        component: () => import('@/views/negotiations/NegotiationsListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.negotiations' },
      },
      {
        path: 'negotiations/new',
        name: 'negotiation-create',
        component: () => import('@/views/negotiations/NegotiationCreateView.vue'),
        meta: { requiresAuth: true, titleKey: 'negotiations.create' },
      },
      {
        path: 'negotiations/:id',
        name: 'negotiation-detail',
        component: () => import('@/views/negotiations/NegotiationDetailView.vue'),
        meta: { requiresAuth: true, titleKey: 'negotiations.detailTitle' },
      },
      {
        path: 'approvals',
        name: 'approvals',
        component: () => import('@/views/approvals/ApprovalsListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.approvals' },
      },
      {
        path: 'agreements',
        name: 'agreements',
        component: () => import('@/views/agreements/AgreementsListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.agreements' },
      },
      {
        path: 'agreements/:id',
        name: 'agreement-detail',
        component: () => import('@/views/agreements/AgreementDetailView.vue'),
        meta: { requiresAuth: true, titleKey: 'agreements.detailTitle' },
      },
      {
        path: 'audit',
        name: 'audit',
        component: () => import('@/views/audit/AuditListView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.audit' },
      },
      {
        path: 'help',
        name: 'help',
        component: () => import('@/views/help/HelpView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.help' },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { requiresAuth: true, titleKey: 'nav.profile' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

setupRouterGuards(router)
export default router
