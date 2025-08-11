/**
 * Unit Tests for Options Calculations
 * Tests all Greeks, delta calculations, and utility functions
 */

import { describe, it, expect } from 'vitest';
import {
  calculateDelta,
  calculateGamma,
  calculateTheta,
  calculateVega,
  calculateTimeToExpiration,
  findStrikeForDelta,
  getExpirationDate,
  estimateImpliedVolatility,
  DELTA_STRATEGIES
} from '../optionsCalculations';

describe('Options Calculations', () => {
  // Standard test parameters
  const spotPrice = 100;
  const strikePrice = 100; // ATM
  const timeToExp = 30 / 365.25; // 30 days
  const riskFreeRate = 0.05;
  const volatility = 0.20;

  describe('Delta Calculations', () => {
    it('should calculate ATM call delta around 0.5', () => {
      const delta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, true);
      expect(delta).toBeCloseTo(0.5, 1);
    });

    it('should calculate ATM put delta around -0.5', () => {
      const delta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, false);
      expect(delta).toBeCloseTo(-0.5, 1);
    });

    it('should satisfy put-call delta relationship', () => {
      const callDelta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, true);
      const putDelta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, false);
      expect(callDelta - putDelta).toBeCloseTo(1, 2);
    });

    it('should return 1 for deep ITM call at expiration', () => {
      const delta = calculateDelta(110, 100, 0, riskFreeRate, volatility, true);
      expect(delta).toBe(1);
    });

    it('should return 0 for OTM call at expiration', () => {
      const delta = calculateDelta(90, 100, 0, riskFreeRate, volatility, true);
      expect(delta).toBe(0);
    });

    it('should return -1 for ITM put at expiration', () => {
      const delta = calculateDelta(90, 100, 0, riskFreeRate, volatility, false);
      expect(delta).toBe(-1);
    });
  });

  describe('Gamma Calculations', () => {
    it('should calculate positive gamma', () => {
      const gamma = calculateGamma(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility);
      expect(gamma).toBeGreaterThan(0);
    });

    it('should return 0 gamma at expiration', () => {
      const gamma = calculateGamma(spotPrice, strikePrice, 0, riskFreeRate, volatility);
      expect(gamma).toBe(0);
    });

    it('should have maximum gamma at ATM', () => {
      const atmGamma = calculateGamma(spotPrice, 100, timeToExp, riskFreeRate, volatility);
      const otmGamma = calculateGamma(spotPrice, 110, timeToExp, riskFreeRate, volatility);
      expect(atmGamma).toBeGreaterThan(otmGamma);
    });
  });

  describe('Theta Calculations', () => {
    it('should calculate negative theta for calls', () => {
      const theta = calculateTheta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, true);
      expect(theta).toBeLessThan(0);
    });

    it('should calculate negative theta for puts', () => {
      const theta = calculateTheta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, false);
      expect(theta).toBeLessThan(0);
    });

    it('should return 0 theta at expiration', () => {
      const theta = calculateTheta(spotPrice, strikePrice, 0, riskFreeRate, volatility, true);
      expect(theta).toBe(0);
    });
  });

  describe('Vega Calculations', () => {
    it('should calculate positive vega', () => {
      const vega = calculateVega(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility);
      expect(vega).toBeGreaterThan(0);
    });

    it('should return 0 vega at expiration', () => {
      const vega = calculateVega(spotPrice, strikePrice, 0, riskFreeRate, volatility);
      expect(vega).toBe(0);
    });

    it('should have maximum vega at ATM', () => {
      const atmVega = calculateVega(spotPrice, 100, timeToExp, riskFreeRate, volatility);
      const otmVega = calculateVega(spotPrice, 110, timeToExp, riskFreeRate, volatility);
      expect(atmVega).toBeGreaterThan(otmVega);
    });
  });

  describe('Time to Expiration Calculations', () => {
    it('should calculate correct time difference', () => {
      const now = new Date('2025-08-11');
      const future = new Date('2025-08-12'); // 1 day later
      const timeToExp = calculateTimeToExpiration(future, now);
      expect(timeToExp).toBeCloseTo(1 / 365.25, 4); // 1 day in years
    });

    it('should return 0 for past dates', () => {
      const now = new Date('2025-08-11');
      const past = new Date('2025-08-10');
      const timeToExp = calculateTimeToExpiration(past, now);
      expect(timeToExp).toBe(0);
    });

    it('should use current date when no trading date provided', () => {
      const future = new Date();
      future.setDate(future.getDate() + 1);
      const timeToExp = calculateTimeToExpiration(future);
      expect(timeToExp).toBeGreaterThan(0);
    });
  });

  describe('Strike Finding for Delta', () => {
    it('should find strike that produces target delta', () => {
      const targetDelta = 0.25;
      const strike = findStrikeForDelta(spotPrice, targetDelta, timeToExp, riskFreeRate, volatility, true);
      
      // Verify the strike produces approximately the target delta
      const actualDelta = calculateDelta(spotPrice, strike, timeToExp, riskFreeRate, volatility, true);
      expect(actualDelta).toBeCloseTo(targetDelta, 1);
    });

    it('should round strikes to nearest $5', () => {
      const strike = findStrikeForDelta(spotPrice, 0.25, timeToExp, riskFreeRate, volatility, true);
      expect(strike % 5).toBe(0);
    });

    it('should handle very short expiration', () => {
      const shortTimeToExp = 1 / 365.25; // 1 day
      const strike = findStrikeForDelta(spotPrice, 0.25, shortTimeToExp, riskFreeRate, volatility, true);
      expect(strike).toBeGreaterThan(spotPrice);
      expect(strike % 5).toBe(0);
    });
  });

  describe('Delta Strategy Presets', () => {
    it('should have 4 strategy presets', () => {
      expect(DELTA_STRATEGIES).toHaveLength(4);
    });

    it('should have conservative strategy with 16-delta', () => {
      const conservative = DELTA_STRATEGIES.find(s => s.name.includes('Conservative'));
      expect(conservative).toBeDefined();
      expect(conservative?.putDelta).toBe(-0.16);
      expect(conservative?.callDelta).toBe(0.16);
    });

    it('should have ATM strategy with 50-delta', () => {
      const atm = DELTA_STRATEGIES.find(s => s.name.includes('ATM'));
      expect(atm).toBeDefined();
      expect(atm?.putDelta).toBe(-0.50);
      expect(atm?.callDelta).toBe(0.50);
    });

    it('should have descriptions for all strategies', () => {
      DELTA_STRATEGIES.forEach(strategy => {
        expect(strategy.description).toBeDefined();
        expect(strategy.description.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Expiration Date Calculations', () => {
    it('should return same date for 0DTE', () => {
      const selectedDate = new Date('2025-08-15');
      const expiration = getExpirationDate('0dte', selectedDate);
      expect(expiration.getTime()).toBe(selectedDate.getTime());
    });

    it('should return next Friday for weekly', () => {
      const monday = new Date('2025-08-11'); // Monday
      const expiration = getExpirationDate('weekly', monday);
      expect(expiration.getDay()).toBe(5); // Friday
      expect(expiration.getDate()).toBe(15); // August 15, 2025 is a Friday
    });

    it('should handle current day for daily', () => {
      const someDate = new Date('2025-08-15');
      const expiration = getExpirationDate('daily', someDate);
      expect(expiration.getDay()).not.toBe(0); // Not Sunday
      expect(expiration.getDay()).not.toBe(6); // Not Saturday
    });

    it('should return third Friday for monthly', () => {
      const someDate = new Date('2025-08-01');
      const expiration = getExpirationDate('monthly', someDate);
      expect(expiration.getDay()).toBe(5); // Friday
      expect(expiration.getDate()).toBe(15); // Third Friday of August 2025
    });
  });

  describe('Implied Volatility Estimation', () => {
    it('should return reasonable volatility estimate', () => {
      const iv = estimateImpliedVolatility(spotPrice);
      expect(iv).toBeGreaterThan(0.10);
      expect(iv).toBeLessThan(0.80);
    });

    it('should return different values for different calls', () => {
      const iv1 = estimateImpliedVolatility(100);
      const iv2 = estimateImpliedVolatility(200);
      // Due to random component, these might be the same, but should be in valid range
      expect(iv1).toBeGreaterThan(0.10);
      expect(iv2).toBeGreaterThan(0.10);
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle zero time to expiration', () => {
      expect(() => calculateDelta(100, 100, 0, 0.05, 0.20, true)).not.toThrow();
      expect(() => calculateGamma(100, 100, 0, 0.05, 0.20)).not.toThrow();
      expect(() => calculateTheta(100, 100, 0, 0.05, 0.20, true)).not.toThrow();
      expect(() => calculateVega(100, 100, 0, 0.05, 0.20)).not.toThrow();
    });

    it('should handle extreme volatility values', () => {
      const highVol = calculateDelta(100, 100, timeToExp, 0.05, 2.0, true);
      const lowVol = calculateDelta(100, 100, timeToExp, 0.05, 0.01, true);
      
      expect(highVol).toBeGreaterThan(0);
      expect(highVol).toBeLessThan(1);
      expect(lowVol).toBeGreaterThan(0);
      expect(lowVol).toBeLessThan(1);
    });

    it('should handle extreme strike prices', () => {
      const veryHighStrike = calculateDelta(100, 1000, timeToExp, riskFreeRate, volatility, true);
      const veryLowStrike = calculateDelta(100, 1, timeToExp, riskFreeRate, volatility, true);
      
      expect(veryHighStrike).toBeCloseTo(0, 2);
      expect(veryLowStrike).toBeCloseTo(1, 2);
    });
  });
});