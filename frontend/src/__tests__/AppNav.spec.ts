import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppNav from '@/components/AppNav.vue'

const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div/>' } }] })

describe('AppNav', () => {
  it('renders navigation links', () => {
    const wrapper = mount(AppNav, {
      global: { plugins: [createPinia(), router] },
    })
    expect(wrapper.text()).toContain('Career Advisor')
    expect(wrapper.text()).toContain('Dashboard')
    expect(wrapper.text()).toContain('Recommendations')
  })
})
