/**
 * Accuracy Verification Utilities
 * Used to verify all frontend display calculations are correct
 */

export interface VerificationResult {
  name: string;
  expected: string | number;
  actual: string | number;
  passed: boolean;
  error?: string;
}

export class AccuracyVerifier {
  private results: VerificationResult[] = [];
  private enabled: boolean;

  constructor() {
    // Enable in development mode only
    this.enabled = process.env.NODE_ENV === 'development';
  }

  /**
   * Verify a calculation matches expected value
   */
  verify(name: string, actual: any, expected: any): void {
    if (!this.enabled) return;

    const passed = this.compareValues(actual, expected);
    const result: VerificationResult = {
      name,
      expected: this.formatValue(expected),
      actual: this.formatValue(actual),
      passed,
      error: passed ? undefined : `Expected ${expected} but got ${actual}`
    };

    this.results.push(result);
    
    if (!passed) {
      console.warn(`❌ Accuracy Check Failed: ${name}`, result);
    } else {
      console.log(`✅ Accuracy Check Passed: ${name}`, result);
    }
  }

  /**
   * Compare two values with tolerance for floating point
   */
  private compareValues(actual: any, expected: any): boolean {
    // Handle null/undefined
    if (actual === expected) return true;
    
    // Handle numbers with small tolerance
    if (typeof actual === 'number' && typeof expected === 'number') {
      const tolerance = 0.0001;
      return Math.abs(actual - expected) < tolerance;
    }
    
    // Handle strings
    if (typeof actual === 'string' && typeof expected === 'string') {
      return actual.trim() === expected.trim();
    }
    
    // Handle dates
    if (actual instanceof Date && expected instanceof Date) {
      return actual.getTime() === expected.getTime();
    }
    
    return false;
  }

  /**
   * Format value for display
   */
  private formatValue(value: any): string | number {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'number') return Number(value.toFixed(4));
    if (value instanceof Date) return value.toISOString();
    return String(value);
  }

  /**
   * Get all verification results
   */
  getResults(): VerificationResult[] {
    return this.results;
  }

  /**
   * Get summary of verification
   */
  getSummary(): { total: number; passed: number; failed: number; successRate: number } {
    const total = this.results.length;
    const passed = this.results.filter(r => r.passed).length;
    const failed = total - passed;
    const successRate = total > 0 ? (passed / total) * 100 : 0;
    
    return { total, passed, failed, successRate };
  }

  /**
   * Clear all results
   */
  clear(): void {
    this.results = [];
  }

  /**
   * Log summary to console
   */
  logSummary(): void {
    if (!this.enabled) return;
    
    const summary = this.getSummary();
    const emoji = summary.successRate === 100 ? '🎉' : '⚠️';
    
    console.group(`${emoji} Accuracy Verification Summary`);
    console.log(`Total Checks: ${summary.total}`);
    console.log(`Passed: ${summary.passed}`);
    console.log(`Failed: ${summary.failed}`);
    console.log(`Success Rate: ${summary.successRate.toFixed(1)}%`);
    
    if (summary.failed > 0) {
      console.group('Failed Checks:');
      this.results
        .filter(r => !r.passed)
        .forEach(r => console.error(r.name, r));
      console.groupEnd();
    }
    
    console.groupEnd();
  }
}

/**
 * Calculation verification functions
 */
export const Calculations = {
  /**
   * Verify total notional calculation
   */
  totalNotional(contracts: number, price: number): number {
    return contracts * 100 * price;
  },

  /**
   * Verify trading window calculation (time from now to exit)
   */
  tradingWindow(selectedDate: Date, exitTime: string): string {
    const now = new Date();
    const exitDate = new Date(selectedDate);
    const [exitHour, exitMinute] = exitTime.split(':').map(Number);
    exitDate.setHours(exitHour, exitMinute, 0, 0);
    
    const diffMs = exitDate.getTime() - now.getTime();
    
    if (diffMs < 0) return 'Past';
    
    const totalHours = diffMs / (1000 * 60 * 60);
    const days = Math.floor(totalHours / 24);
    const hours = Math.floor(totalHours % 24);
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  },

  /**
   * Verify days to expiration calculation
   */
  daysToExpiration(selectedDate: Date): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(selectedDate);
    target.setHours(0, 0, 0, 0);
    
    const diffMs = target.getTime() - today.getTime();
    const days = Math.round(diffMs / (1000 * 60 * 60 * 24));
    return Math.max(0, days);
  },

  /**
   * Verify strike distance calculation
   */
  strikeDistance(strike: number, currentPrice: number): { 
    distance: number; 
    percentage: number; 
    formatted: string;
  } {
    const distance = strike - currentPrice;
    const percentage = (distance / currentPrice) * 100;
    const formatted = `${distance > 0 ? '+' : ''}${distance.toFixed(2)} (${percentage.toFixed(1)}%)`;
    
    return { distance, percentage, formatted };
  },

  /**
   * Verify spread width calculation
   */
  spreadWidth(upperStrike: number, lowerStrike: number): number {
    return upperStrike - lowerStrike;
  },

  /**
   * Format date for display
   */
  formatDate(date: Date): string {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    return `${month}/${day}/${year}`;
  },

  /**
   * Get day of week
   */
  getDayOfWeek(date: Date): string {
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  },

  /**
   * Verify currency formatting
   */
  formatCurrency(amount: number): string {
    return `$${Math.round(amount).toLocaleString()}`;
  },

  /**
   * Verify percentage formatting
   */
  formatPercentage(value: number, decimals: number = 1): string {
    return `${value.toFixed(decimals)}%`;
  },

  /**
   * Verify delta formatting
   */
  formatDelta(delta: number): string {
    return `Δ${Math.round(Math.abs(delta) * 100)}`;
  },

  /**
   * Check if date is weekend
   */
  isWeekend(date: Date): boolean {
    const day = date.getDay();
    return day === 0 || day === 6;
  },

  /**
   * Check if date is past
   */
  isPastDate(date: Date): boolean {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(date);
    target.setHours(0, 0, 0, 0);
    return target < today;
  },

  /**
   * Test Black-Scholes Greeks calculations with known values
   */
  testGreeksCalculations(): {
    testScenario: string;
    expected: {
      callDelta: number;
      putDelta: number;
      gamma: number;
      callTheta: number;
      putTheta: number;
      vega: number;
    };
  } {
    // ATM option with 30 days to expiration - predictable Greeks values
    return {
      testScenario: "ATM option, 30 days, 20% vol, 5% rate",
      expected: {
        callDelta: 0.5, // ATM call delta ~0.5
        putDelta: -0.5, // ATM put delta ~-0.5  
        gamma: 0.02, // Gamma peaks at ATM
        callTheta: -0.04, // Negative time decay per day
        putTheta: -0.04, // Similar theta for puts
        vega: 0.08 // Vega for 1% vol change
      }
    };
  },

  /**
   * Verify delta strategy calculations
   */
  verifyDeltaStrategy(
    currentPrice: number,
    targetDelta: number,
    isCall: boolean,
    timeToExpiration: number
  ): number {
    // Simplified strike estimation based on delta
    // For 0DTE or very short expiration, use percentage-based approach
    if (timeToExpiration < 0.02) { // Less than ~7 days
      if (isCall) {
        const percentageOTM = (1 - targetDelta) * 0.03; // Rough approximation
        return Math.round((currentPrice * (1 + percentageOTM)) / 5) * 5;
      } else {
        const percentageOTM = Math.abs(targetDelta) * 0.03;
        return Math.round((currentPrice * (1 - percentageOTM)) / 5) * 5;
      }
    }
    
    // For longer expiration, would use binary search (simplified here)
    return currentPrice; // Placeholder - would implement full calculation
  }
};

// Export singleton instance
export const verifier = new AccuracyVerifier();