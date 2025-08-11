/**
 * Greeks Testing Suite for Options Calculations
 * Tests Delta, Gamma, Theta, Vega accuracy against known values
 */

import { calculateDelta, calculateGamma, calculateTheta, calculateVega, findStrikeForDelta, DELTA_STRATEGIES } from './optionsCalculations';
import { verifier, Calculations } from './accuracyVerification';

export function runGreeksTests() {
  console.group('🧮 Greeks Calculations Testing');
  
  // Standard test parameters - ATM option with 30 days
  const spotPrice = 100;
  const strikePrice = 100; // ATM
  const timeToExp = 30 / 365.25; // 30 days in years
  const riskFreeRate = 0.05; // 5%
  const volatility = 0.20; // 20%
  
  // Test 1: Delta Calculations
  const callDelta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, true);
  const putDelta = calculateDelta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, false);
  
  // ATM call delta should be ~0.5, put delta should be ~-0.5
  verifier.verify('ATM Call Delta ~0.5', Math.abs(callDelta - 0.5) < 0.1, true);
  verifier.verify('ATM Put Delta ~-0.5', Math.abs(putDelta + 0.5) < 0.1, true);
  verifier.verify('Put-Call Delta Relationship', Math.abs((callDelta - putDelta) - 1) < 0.01, true);
  
  // Test 2: Gamma Calculations
  const gamma = calculateGamma(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility);
  
  // Gamma should be positive and peak at ATM
  verifier.verify('Gamma is Positive', gamma > 0, true);
  verifier.verify('ATM Gamma Reasonable Range', gamma > 0.005 && gamma < 0.05, true);
  
  // Test 3: Theta Calculations
  const callTheta = calculateTheta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, true);
  const putTheta = calculateTheta(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility, false);
  
  // Theta should be negative (time decay)
  verifier.verify('Call Theta is Negative', callTheta < 0, true);
  verifier.verify('Put Theta is Negative', putTheta < 0, true);
  verifier.verify('Theta Reasonable Range', Math.abs(callTheta) > 0.01 && Math.abs(callTheta) < 0.1, true);
  
  // Test 4: Vega Calculations
  const vega = calculateVega(spotPrice, strikePrice, timeToExp, riskFreeRate, volatility);
  
  // Vega should be positive for both calls and puts
  verifier.verify('Vega is Positive', vega > 0, true);
  verifier.verify('Vega Reasonable Range', vega > 0.01 && vega < 0.2, true);
  
  // Test 5: Edge Case - At Expiration
  const expiredCallDelta = calculateDelta(spotPrice, strikePrice, 0, riskFreeRate, volatility, true);
  const expiredGamma = calculateGamma(spotPrice, strikePrice, 0, riskFreeRate, volatility);
  const expiredTheta = calculateTheta(spotPrice, strikePrice, 0, riskFreeRate, volatility, true);
  const expiredVega = calculateVega(spotPrice, strikePrice, 0, riskFreeRate, volatility);
  
  verifier.verify('Expired ATM Call Delta', expiredCallDelta, 1); // ITM at expiration
  verifier.verify('Expired Gamma', expiredGamma, 0);
  verifier.verify('Expired Theta', expiredTheta, 0);
  verifier.verify('Expired Vega', expiredVega, 0);
  
  // Test 6: Deep ITM/OTM Behavior
  const deepITMCallDelta = calculateDelta(spotPrice, 80, timeToExp, riskFreeRate, volatility, true); // Deep ITM
  const deepOTMCallDelta = calculateDelta(spotPrice, 120, timeToExp, riskFreeRate, volatility, true); // Deep OTM
  
  verifier.verify('Deep ITM Call Delta Near 1', deepITMCallDelta > 0.8, true);
  verifier.verify('Deep OTM Call Delta Near 0', deepOTMCallDelta < 0.2, true);
  
  // Test 7: Delta Strategy Presets
  console.group('Delta Strategy Presets Testing');
  
  DELTA_STRATEGIES.forEach(strategy => {
    if (strategy.callDelta && strategy.putDelta) {
      // Test that findStrikeForDelta produces reasonable strikes
      const callStrike = findStrikeForDelta(spotPrice, strategy.callDelta, timeToExp, riskFreeRate, volatility, true);
      const putStrike = findStrikeForDelta(spotPrice, Math.abs(strategy.putDelta), timeToExp, riskFreeRate, volatility, false);
      
      // Verify strikes are reasonable
      verifier.verify(`${strategy.name} Call Strike > Current`, callStrike > spotPrice, true);
      verifier.verify(`${strategy.name} Put Strike < Current`, putStrike < spotPrice, true);
      verifier.verify(`${strategy.name} Strike Rounding`, callStrike % 5 === 0, true);
      
      // Verify the calculated strikes produce approximately the target delta
      const actualCallDelta = calculateDelta(spotPrice, callStrike, timeToExp, riskFreeRate, volatility, true);
      const actualPutDelta = calculateDelta(spotPrice, putStrike, timeToExp, riskFreeRate, volatility, false);
      
      const callDeltaTolerance = Math.abs(actualCallDelta - strategy.callDelta) < 0.1;
      const putDeltaTolerance = Math.abs(actualPutDelta - strategy.putDelta) < 0.1;
      
      verifier.verify(`${strategy.name} Call Delta Accuracy`, callDeltaTolerance, true);
      verifier.verify(`${strategy.name} Put Delta Accuracy`, putDeltaTolerance, true);
    }
  });
  
  console.groupEnd();
  
  // Test 8: Greeks Consistency Tests
  // Test that Greeks behave consistently across different scenarios
  const scenarios = [
    { spot: 90, strike: 100, name: "OTM Call" },
    { spot: 100, strike: 100, name: "ATM Call" },
    { spot: 110, strike: 100, name: "ITM Call" }
  ];
  
  scenarios.forEach(scenario => {
    const delta = calculateDelta(scenario.spot, scenario.strike, timeToExp, riskFreeRate, volatility, true);
    const gamma = calculateGamma(scenario.spot, scenario.strike, timeToExp, riskFreeRate, volatility);
    const theta = calculateTheta(scenario.spot, scenario.strike, timeToExp, riskFreeRate, volatility, true);
    const vega = calculateVega(scenario.spot, scenario.strike, timeToExp, riskFreeRate, volatility);
    
    // Basic sanity checks
    verifier.verify(`${scenario.name} Delta in Range [0,1]`, delta >= 0 && delta <= 1, true);
    verifier.verify(`${scenario.name} Gamma >= 0`, gamma >= 0, true);
    verifier.verify(`${scenario.name} Theta <= 0`, theta <= 0, true);
    verifier.verify(`${scenario.name} Vega >= 0`, vega >= 0, true);
  });
  
  // Log summary
  const summary = verifier.getSummary();
  console.log(`Greeks Tests Complete: ${summary.passed}/${summary.total} passed`);
  console.groupEnd();
  
  return summary;
}

export default runGreeksTests;