/**
 * Market utilities for checking market status and hours
 */

export interface MarketStatus {
	isOpen: boolean
	status: 'pre-market' | 'open' | 'after-hours' | 'closed'
	nextOpen?: Date
	nextClose?: Date
	timeUntilOpen?: string
	timeUntilClose?: string
}

/**
 * Check if the US stock market is currently open
 * NYSE/NASDAQ hours: 9:30 AM - 4:00 PM ET, Monday-Friday
 * Accounts for weekends and basic holidays
 */
export function getMarketStatus(): MarketStatus {
	const now = new Date()
	
	// Convert to ET (Eastern Time)
	// Note: This is a simplified conversion. In production, use a proper timezone library
	const etOffset = getETOffset(now)
	const etHours = new Date(now.getTime() + etOffset * 60 * 60 * 1000)
	
	const dayOfWeek = etHours.getUTCDay()
	const hour = etHours.getUTCHours()
	const minute = etHours.getUTCMinutes()
	const currentTime = hour * 60 + minute // Convert to minutes for easier comparison
	
	// Market hours in ET (converted to minutes)
	const preMarketStart = 4 * 60    // 4:00 AM ET
	const marketOpen = 9 * 60 + 30   // 9:30 AM ET
	const marketClose = 16 * 60      // 4:00 PM ET
	const afterHoursEnd = 20 * 60    // 8:00 PM ET
	
	// Check if weekend (Saturday = 6, Sunday = 0)
	if (dayOfWeek === 0 || dayOfWeek === 6) {
		return {
			isOpen: false,
			status: 'closed',
			nextOpen: getNextMarketOpen(etHours),
			timeUntilOpen: getTimeUntilOpen(etHours)
		}
	}
	
	// Check if it's a major US market holiday
	if (isMarketHoliday(etHours)) {
		return {
			isOpen: false,
			status: 'closed',
			nextOpen: getNextMarketOpen(etHours),
			timeUntilOpen: getTimeUntilOpen(etHours)
		}
	}
	
	// Check time of day
	if (currentTime < preMarketStart) {
		// Before pre-market
		return {
			isOpen: false,
			status: 'closed',
			nextOpen: getNextMarketOpen(etHours),
			timeUntilOpen: getTimeUntilOpen(etHours)
		}
	} else if (currentTime >= preMarketStart && currentTime < marketOpen) {
		// Pre-market hours
		return {
			isOpen: false,
			status: 'pre-market',
			nextOpen: getTodayMarketOpen(etHours),
			timeUntilOpen: getTimeUntilMarketOpen(etHours)
		}
	} else if (currentTime >= marketOpen && currentTime < marketClose) {
		// Market is open!
		return {
			isOpen: true,
			status: 'open',
			nextClose: getTodayMarketClose(etHours),
			timeUntilClose: getTimeUntilMarketClose(etHours)
		}
	} else if (currentTime >= marketClose && currentTime < afterHoursEnd) {
		// After-hours trading
		return {
			isOpen: false,
			status: 'after-hours',
			nextOpen: getNextMarketOpen(etHours),
			timeUntilOpen: getTimeUntilOpen(etHours)
		}
	} else {
		// After after-hours (8 PM ET or later)
		return {
			isOpen: false,
			status: 'closed',
			nextOpen: getNextMarketOpen(etHours),
			timeUntilOpen: getTimeUntilOpen(etHours)
		}
	}
}

/**
 * Get ET offset from UTC (accounts for EST/EDT)
 * EST = UTC-5, EDT = UTC-4
 */
function getETOffset(date: Date): number {
	// Simplified: This assumes EDT (UTC-4) from March to November, EST (UTC-5) otherwise
	// In production, use a proper timezone library like date-fns-tz
	const month = date.getMonth()
	const isDST = month >= 2 && month <= 10 // March (2) through November (10)
	return isDST ? -4 : -5
}

/**
 * Check if the given date is a US market holiday
 * This is a simplified check for major holidays
 */
function isMarketHoliday(date: Date): boolean {
	const year = date.getUTCFullYear()
	const month = date.getUTCMonth()
	const day = date.getUTCDate()
	
	// Major US market holidays (simplified - doesn't account for observed dates)
	const holidays = [
		{ month: 0, day: 1 },   // New Year's Day
		{ month: 0, day: 15 },  // MLK Day (approximate - 3rd Monday)
		{ month: 1, day: 19 },  // Presidents Day (approximate - 3rd Monday)
		{ month: 3, day: 14 },  // Good Friday (approximate - varies)
		{ month: 4, day: 27 },  // Memorial Day (approximate - last Monday)
		{ month: 6, day: 4 },   // Independence Day
		{ month: 8, day: 2 },   // Labor Day (approximate - 1st Monday)
		{ month: 10, day: 28 }, // Thanksgiving (approximate - 4th Thursday)
		{ month: 11, day: 25 }  // Christmas
	]
	
	return holidays.some(h => h.month === month && Math.abs(h.day - day) <= 3)
}

/**
 * Get the next market open time
 */
function getNextMarketOpen(currentET: Date): Date {
	const next = new Date(currentET)
	const dayOfWeek = next.getUTCDay()
	const hour = next.getUTCHours()
	
	// If it's before 9:30 AM on a weekday, market opens today
	if (dayOfWeek >= 1 && dayOfWeek <= 5 && hour < 9.5) {
		next.setUTCHours(9, 30, 0, 0)
		return next
	}
	
	// Otherwise, find next weekday
	do {
		next.setUTCDate(next.getUTCDate() + 1)
		next.setUTCHours(9, 30, 0, 0)
	} while (next.getUTCDay() === 0 || next.getUTCDay() === 6)
	
	return next
}

/**
 * Get today's market open time (9:30 AM ET)
 */
function getTodayMarketOpen(currentET: Date): Date {
	const open = new Date(currentET)
	open.setUTCHours(9, 30, 0, 0)
	return open
}

/**
 * Get today's market close time (4:00 PM ET)
 */
function getTodayMarketClose(currentET: Date): Date {
	const close = new Date(currentET)
	close.setUTCHours(16, 0, 0, 0)
	return close
}

/**
 * Get time until next market open as a formatted string
 */
function getTimeUntilOpen(currentET: Date): string {
	const nextOpen = getNextMarketOpen(currentET)
	const diff = nextOpen.getTime() - currentET.getTime()
	return formatTimeDiff(diff)
}

/**
 * Get time until today's market open
 */
function getTimeUntilMarketOpen(currentET: Date): string {
	const marketOpen = getTodayMarketOpen(currentET)
	const diff = marketOpen.getTime() - currentET.getTime()
	return formatTimeDiff(diff)
}

/**
 * Get time until market close
 */
function getTimeUntilMarketClose(currentET: Date): string {
	const marketClose = getTodayMarketClose(currentET)
	const diff = marketClose.getTime() - currentET.getTime()
	return formatTimeDiff(diff)
}

/**
 * Format time difference as human-readable string
 */
function formatTimeDiff(milliseconds: number): string {
	const seconds = Math.floor(milliseconds / 1000)
	const minutes = Math.floor(seconds / 60)
	const hours = Math.floor(minutes / 60)
	const days = Math.floor(hours / 24)
	
	if (days > 0) {
		const remainingHours = hours % 24
		return `${days}d ${remainingHours}h`
	} else if (hours > 0) {
		const remainingMinutes = minutes % 60
		return `${hours}h ${remainingMinutes}m`
	} else {
		return `${minutes}m`
	}
}