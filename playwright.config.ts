import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
	testDir: './tests/e2e',
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	workers: process.env.CI ? 1 : undefined,
	reporter: 'html',
	use: {
		baseURL: 'http://localhost:3001',
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
	},

	projects: [
		{
			name: 'chromium',
			use: { ...devices['Desktop Chrome'] },
		},
		{
			name: 'Mobile Chrome',
			use: { ...devices['Pixel 5'] },
		},
	],

	webServer: [
		{
			command: 'npm run dev',
			url: 'http://localhost:3001',
			reuseExistingServer: true,
			timeout: 120 * 1000,
		},
		{
			command: 'uv run -m uvicorn api.main:app --host 127.0.0.1 --port 8001',
			url: 'http://127.0.0.1:8001/health',
			reuseExistingServer: true,
			timeout: 120 * 1000,
		},
	],
})