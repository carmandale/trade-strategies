// Options calculations utilities for delta, pricing, and strike selection

// Standard normal cumulative distribution function approximation
function normalCDF(x: number): number {
  const a1 =  0.254829592;
  const a2 = -0.284496736;
  const a3 =  1.421413741;
  const a4 = -1.453152027;
  const a5 =  1.061405429;
  const p  =  0.3275911;

  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x) / Math.sqrt(2);

  const t = 1.0 / (1.0 + p * x);
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

  return 0.5 * (1.0 + sign * y);
}

// Black-Scholes delta calculation for options
export function calculateDelta(
  spotPrice: number,
  strikePrice: number,
  timeToExpiration: number, // in years
  riskFreeRate: number = 0.05, // 5% default
  volatility: number = 0.20, // 20% default for SPY
  isCall: boolean = true
): number {
  if (timeToExpiration <= 0) {
    // At expiration, delta is either 0 or 1
    if (isCall) {
      return spotPrice > strikePrice ? 1 : 0;
    } else {
      return spotPrice < strikePrice ? -1 : 0;
    }
  }

  const d1 = (Math.log(spotPrice / strikePrice) + (riskFreeRate + 0.5 * volatility * volatility) * timeToExpiration) / 
             (volatility * Math.sqrt(timeToExpiration));

  if (isCall) {
    return normalCDF(d1);
  } else {
    return normalCDF(d1) - 1; // Put delta = Call delta - 1
  }
}

// Calculate time to expiration in years from current date to expiration date
export function calculateTimeToExpiration(expirationDate: Date): number {
  const now = new Date();
  const msPerYear = 365.25 * 24 * 60 * 60 * 1000;
  const timeMs = expirationDate.getTime() - now.getTime();
  return Math.max(0, timeMs / msPerYear);
}

// Find strike price that gives target delta
export function findStrikeForDelta(
  spotPrice: number,
  targetDelta: number,
  timeToExpiration: number,
  riskFreeRate: number = 0.05,
  volatility: number = 0.20,
  isCall: boolean = true
): number {
  // Use binary search to find strike that produces target delta
  let lowStrike = spotPrice * 0.5;
  let highStrike = spotPrice * 1.5;
  
  for (let i = 0; i < 50; i++) { // 50 iterations should give us good precision
    const midStrike = (lowStrike + highStrike) / 2;
    const delta = calculateDelta(spotPrice, midStrike, timeToExpiration, riskFreeRate, volatility, isCall);
    
    const targetDiff = isCall ? delta - targetDelta : delta - targetDelta;
    
    if (Math.abs(targetDiff) < 0.001) {
      return Math.round(midStrike / 5) * 5; // Round to nearest $5
    }
    
    if (targetDiff > 0) {
      if (isCall) {
        lowStrike = midStrike; // For calls, higher strike = lower delta
      } else {
        highStrike = midStrike; // For puts, higher strike = more negative delta
      }
    } else {
      if (isCall) {
        highStrike = midStrike;
      } else {
        lowStrike = midStrike;
      }
    }
  }
  
  return Math.round(((lowStrike + highStrike) / 2) / 5) * 5;
}

// Get expiration date for different timeframes
export function getExpirationDate(timeframe: 'daily' | 'weekly' | 'monthly'): Date {
  const now = new Date();
  const expiration = new Date(now);
  
  switch (timeframe) {
    case 'daily':
      // Next trading day (or same day if before 4pm ET)
      if (now.getHours() >= 16) {
        expiration.setDate(now.getDate() + 1);
      }
      // Skip weekends
      while (expiration.getDay() === 0 || expiration.getDay() === 6) {
        expiration.setDate(expiration.getDate() + 1);
      }
      break;
      
    case 'weekly':
      // Next Friday
      const daysUntilFriday = (5 - now.getDay() + 7) % 7;
      expiration.setDate(now.getDate() + (daysUntilFriday || 7));
      break;
      
    case 'monthly':
      // Third Friday of current or next month
      const thirdFriday = getThirdFriday(now.getFullYear(), now.getMonth());
      if (thirdFriday <= now) {
        // Use next month's third Friday
        const nextMonth = now.getMonth() === 11 ? 0 : now.getMonth() + 1;
        const nextYear = now.getMonth() === 11 ? now.getFullYear() + 1 : now.getFullYear();
        expiration.setTime(getThirdFriday(nextYear, nextMonth).getTime());
      } else {
        expiration.setTime(thirdFriday.getTime());
      }
      break;
  }
  
  return expiration;
}

// Helper function to get third Friday of a month
function getThirdFriday(year: number, month: number): Date {
  const firstDay = new Date(year, month, 1);
  const firstDayOfWeek = firstDay.getDay();
  const firstFriday = new Date(year, month, 1 + (5 - firstDayOfWeek + 7) % 7);
  // Third Friday is 14 days after the first Friday
  return new Date(year, month, firstFriday.getDate() + 14);
}

// Calculate implied volatility (simplified estimate)
export function estimateImpliedVolatility(spotPrice: number): number {
  // Simple estimate based on VIX-like calculation
  // In real implementation, you'd fetch actual IV from options chain
  const baseVol = 0.20; // 20% base volatility
  const vixEstimate = Math.max(0.10, Math.min(0.80, baseVol + (Math.random() - 0.5) * 0.10));
  return vixEstimate;
}

// Delta-based strike selection strategies
export interface DeltaStrategy {
  name: string;
  putDelta?: number;
  callDelta?: number;
  description: string;
}

export const DELTA_STRATEGIES: DeltaStrategy[] = [
  {
    name: "Conservative (16-Delta)",
    putDelta: -0.16,
    callDelta: 0.16,
    description: "High probability trades, ~84% success rate"
  },
  {
    name: "Moderate (25-Delta)", 
    putDelta: -0.25,
    callDelta: 0.25,
    description: "Balanced risk/reward, ~75% success rate"
  },
  {
    name: "Aggressive (35-Delta)",
    putDelta: -0.35,
    callDelta: 0.35,
    description: "Higher premium, ~65% success rate"
  },
  {
    name: "ATM (50-Delta)",
    putDelta: -0.50,
    callDelta: 0.50,
    description: "At-the-money, maximum time decay"
  }
];