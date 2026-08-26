/**
 * Unit tests for HomePage component.
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'

// Create a minimal router for testing
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/login', component: { template: '<div>Login</div>' } },
    { path: '/register', component: { template: '<div>Register</div>' } },
  ],
})

describe('HomePage', () => {
  it('renders the title', async () => {
    router.push('/')
    await router.isReady()

    const wrapper = mount(HomePage, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('Legatio AI')
  })

  it('renders the tagline', async () => {
    router.push('/')
    await router.isReady()

    const wrapper = mount(HomePage, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('Your AI agent. Your rules.')
  })

  it('has Get Started and Sign In buttons', async () => {
    router.push('/')
    await router.isReady()

    const wrapper = mount(HomePage, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('Get Started')
    expect(wrapper.text()).toContain('Sign In')
  })
})
