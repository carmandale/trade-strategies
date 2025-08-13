// Setup file for Vitest tests
import '@testing-library/jest-dom'
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Clean up after each test case
afterEach(() => {
  cleanup()
})

// Mock fetch API
global.fetch = vi.fn().mockImplementation(() => 
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
)

// Mock console.error to avoid polluting test output
console.error = vi.fn()

// Mock environment variables
process.env.VITE_API_URL = 'http://localhost:8001'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Polyfill ResizeObserver for Recharts ResponsiveContainer in JSDOM
class ResizeObserverMock {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target?: Element) {
    // Immediately invoke to simulate first measurement with complete entry for Radix UI
    const sizeEntry = {
      inlineSize: 800,
      blockSize: 600
    }
    const entry = {
      target: target ?? ({} as Element),
      contentRect: { width: 800, height: 600, x: 0, y: 0, top: 0, left: 0, bottom: 600, right: 800 },
      borderBoxSize: [sizeEntry],
      contentBoxSize: [sizeEntry],
      devicePixelContentBoxSize: [sizeEntry],
    } as unknown as ResizeObserverEntry
    this.callback([entry], this as unknown as ResizeObserver)
  }
  unobserve() {}
  disconnect() {}
}

if (typeof globalThis.ResizeObserver === 'undefined') {
  ;(globalThis as any).ResizeObserver = ResizeObserverMock
}

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Polyfill for pointer capture methods needed by Radix UI
if (typeof Element !== 'undefined' && !Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = function () {
    return false
  }
  Element.prototype.setPointerCapture = function () {
    // no-op
  }
  Element.prototype.releasePointerCapture = function () {
    // no-op
  }
}
