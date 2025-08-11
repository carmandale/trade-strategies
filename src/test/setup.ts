import '@testing-library/jest-dom'
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Clean up after each test case
afterEach(() => {
	cleanup()
})

// Polyfill ResizeObserver for Recharts ResponsiveContainer in JSDOM
class ResizeObserverMock {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target?: Element) {
    // Immediately invoke to simulate first measurement with a fake contentRect
    const entry = {
      target: target ?? ({} as Element),
      contentRect: { width: 800, height: 600, x: 0, y: 0, top: 0, left: 0, bottom: 600, right: 800 },
      borderBoxSize: [],
      contentBoxSize: [],
      devicePixelContentBoxSize: [],
    } as unknown as ResizeObserverEntry
    this.callback([entry], this as unknown as ResizeObserver)
  }
  unobserve() {}
  disconnect() {}
}

if (typeof globalThis.ResizeObserver === 'undefined') {
  ;(globalThis as any).ResizeObserver = ResizeObserverMock
}