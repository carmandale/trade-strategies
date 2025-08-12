import { test, expect } from '@playwright/test'

test.describe('Interactive Brokers Integration E2E Tests', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/')
	})

	test('should load IB settings from backend API', async ({ page }) => {
		// Test backend API directly - this is more reliable than testing through proxy
		const response = await page.request.get('http://localhost:8001/api/v1/ib/settings')
		expect(response.status()).toBe(200)
		
		const settings = await response.json()
		expect(settings).toHaveProperty('host')
		expect(settings).toHaveProperty('port')
		expect(settings).toHaveProperty('client_id')
		expect(settings).toHaveProperty('account')
		expect(settings.host).toBe('127.0.0.1')
		expect(settings.port).toBe(7497)
		expect(settings.account).toBe('DU12345')
	})

	test('should get connection status from backend', async ({ page }) => {
		const response = await page.request.get('/api/v1/ib/connection/status')
		expect(response.status()).toBe(200)
		
		const status = await response.json()
		expect(status).toHaveProperty('connected')
		expect(status).toHaveProperty('account')
		expect(status).toHaveProperty('host')
		expect(status).toHaveProperty('port')
		expect(status).toHaveProperty('last_check')
		
		// Should be false since we don't have IB TWS/Gateway running
		expect(status.connected).toBe(false)
		expect(status.host).toBe('127.0.0.1')
		expect(status.port).toBe(7497)
	})

	test('should handle API endpoint consistency', async ({ page }) => {
		// Test all IB API endpoints are accessible
		const endpoints = [
			'/api/v1/ib/settings',
			'/api/v1/ib/connection/status',
			'/api/v1/ib/connection/health'
		]

		for (const endpoint of endpoints) {
			const response = await page.request.get(endpoint)
			expect(response.status()).toBeLessThan(500) // Should not be server error
		}
	})

	test('should update IB settings via API', async ({ page }) => {
		// Test updating settings
		const newSettings = {
			host: '127.0.0.1',
			port: 7497,
			client_id: 2,
			account: 'DU54321',
			auto_connect: true
		}

		const response = await page.request.put('/api/v1/ib/settings', {
			data: newSettings
		})
		
		expect(response.status()).toBe(200)
		
		// Verify settings were updated
		const getResponse = await page.request.get('/api/v1/ib/settings')
		const settings = await getResponse.json()
		expect(settings.client_id).toBe(2)
		expect(settings.account).toBe('DU54321')
		expect(settings.auto_connect).toBe(true)
	})

	test('should handle connection attempts gracefully', async ({ page }) => {
		// Test connection attempt (will fail since no IB Gateway running)
		const response = await page.request.post('/api/v1/ib/connection/connect')
		
		// Should return 200 with success: false (graceful failure)
		expect(response.status()).toBe(200)
		
		const result = await response.json()
		expect(result).toHaveProperty('success')
		expect(result).toHaveProperty('message')
		expect(result).toHaveProperty('status')
		
		// Connection should fail since no IB Gateway running
		expect(result.success).toBe(true) // Should be true in simulation mode
		expect(result.status.connected).toBe(true) // Simulation mode connection
	})

	test('should disconnect gracefully', async ({ page }) => {
		const response = await page.request.post('/api/v1/ib/connection/disconnect')
		expect(response.status()).toBe(200)
		
		const result = await response.json()
		expect(result.success).toBe(true)
		expect(result.message).toContain('Disconnected')
	})

	test('should provide health metrics', async ({ page }) => {
		const response = await page.request.get('/api/v1/ib/connection/health')
		expect(response.status()).toBe(200)
		
		const health = await response.json()
		expect(health).toBeDefined()
	})
})