import { test, expect } from '@playwright/test'

test.describe('Strategy Display E2E Tests', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/')
	})

	test('should load and display strategy dashboard', async ({ page }) => {
		await expect(page.locator('text=SPY Spread Strategies')).toBeVisible()
		await expect(page.locator('text=Bull Call Spread')).toBeVisible()
		await expect(page.locator('text=Iron Condor')).toBeVisible()
		await expect(page.locator('text=Butterfly Spread')).toBeVisible()
		await expect(page.locator('text=Strategy Portfolio')).toBeVisible()
	})

	test('should display real-time price updates', async ({ page }) => {
		const priceElement = page.locator('[data-testid="current-price"]')
		await expect(priceElement).toBeVisible()
		const initialPrice = await priceElement.textContent()
		expect(initialPrice).toBeTruthy()
		await page.waitForTimeout(6000)
		const updatedPrice = await priceElement.textContent()
		expect(updatedPrice).toBeTruthy()
	})

	test('should handle strategy configuration inputs', async ({ page }) => {
		const quantityInput = page.locator('input[placeholder*="Quantity"]')
		await quantityInput.fill('10')
		await expect(quantityInput).toHaveValue('10')

		const expirationButton = page.locator('button:has-text("Select Expiration")')
		await expirationButton.click()
		const expirationOption = page.locator('text=7 days').first()
		await expirationOption.click()
		await expect(expirationButton).not.toHaveText('Select Expiration')
	})

	test('should display strategy visualizations', async ({ page }) => {
		const equityChart = page.locator('[data-testid="equity-curve-chart"]')
		await expect(equityChart).toBeVisible()

		const histogramChart = page.locator('[data-testid="pl-histogram-chart"]')
		await expect(histogramChart).toBeVisible()

		const performanceMetrics = page.locator('[data-testid="performance-metrics"]')
		await expect(performanceMetrics).toBeVisible()

		await expect(page.locator('text=Win Rate')).toBeVisible()
		await expect(page.locator('text=Total P/L')).toBeVisible()
		await expect(page.locator('text=Sharpe Ratio')).toBeVisible()
	})

	test('should switch between strategy timeframes', async ({ page }) => {
		await page.waitForSelector('text=Strategy Portfolio')

		const dailyTab = page.locator('[role="tab"]:has-text("Daily")')
		await dailyTab.click()
		await expect(dailyTab).toHaveAttribute('aria-selected', 'true')

		const weeklyTab = page.locator('[role="tab"]:has-text("Weekly")')
		await weeklyTab.click()
		await expect(weeklyTab).toHaveAttribute('aria-selected', 'true')

		const monthlyTab = page.locator('[role="tab"]:has-text("Monthly")')
		await monthlyTab.click()
		await expect(monthlyTab).toHaveAttribute('aria-selected', 'true')
	})

	test('should handle API errors gracefully', async ({ page, context }) => {
		await context.route('**/api/strategies/**', route => {
			route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ error: 'Internal Server Error' })
			})
		})

		await page.reload()
		await expect(page.locator('text=Error loading strategies')).toBeVisible()
		const retryButton = page.locator('button:has-text("Retry")')
		await expect(retryButton).toBeVisible()
	})

	test('should be responsive on mobile devices', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 })
		const dashboard = page.locator('[data-testid="strategy-dashboard"]')
		await expect(dashboard).toBeVisible()

		const cards = page.locator('[data-testid^="strategy-card-"]')
		const count = await cards.count()
		expect(count).toBeGreaterThan(0)

		const menuButton = page.locator('[aria-label="Menu"]')
		if (await menuButton.isVisible()) {
			await menuButton.click()
			await expect(page.locator('[role="navigation"]')).toBeVisible()
		}
	})
})

test.describe('Performance Tests', () => {
	test('should load initial page within 3 seconds', async ({ page }) => {
		const startTime = Date.now()
		await page.goto('/')
		await page.waitForSelector('text=SPY Spread Strategies')
		const loadTime = Date.now() - startTime
		expect(loadTime).toBeLessThan(3000)
	})

	test('should handle rapid user interactions', async ({ page }) => {
		await page.goto('/')
		for (let i = 0; i < 10; i++) {
			await page.locator('[role="tab"]:has-text("Daily")').click()
			await page.locator('[role="tab"]:has-text("Weekly")').click()
			await page.locator('[role="tab"]:has-text("Monthly")').click()
		}
		await expect(page.locator('text=Strategy Portfolio')).toBeVisible()
	})
})

test.describe('Accessibility Tests', () => {
	test('should have proper ARIA labels', async ({ page }) => {
		await page.goto('/')
		const buttons = page.locator('button')
		const buttonCount = await buttons.count()
		
		for (let i = 0; i < buttonCount; i++) {
			const button = buttons.nth(i)
			const ariaLabel = await button.getAttribute('aria-label')
			const textContent = await button.textContent()
			expect(ariaLabel || textContent).toBeTruthy()
		}
	})

	test('should be keyboard navigable', async ({ page }) => {
		await page.goto('/')
		await page.keyboard.press('Tab')
		await expect(page.locator(':focus')).toBeVisible()

		for (let i = 0; i < 5; i++) {
			await page.keyboard.press('Tab')
			await expect(page.locator(':focus')).toBeVisible()
		}

		await page.keyboard.press('Enter')
	})
})