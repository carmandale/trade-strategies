/**
 * Edge Case Testing for Frontend Accuracy
 * Tests weekend dates, past dates, extreme values, etc.
 */

import { Calculations, verifier } from './accuracyVerification';

export function runEdgeCaseTests() {
  console.group('🧪 Edge Case Testing');
  
  // Test 1: Weekend Date Handling
  const saturday = new Date('2025-08-16'); // Saturday
  const sunday = new Date('2025-08-17'); // Sunday
  
  verifier.verify('Saturday is Weekend', Calculations.isWeekend(saturday), true);
  verifier.verify('Sunday is Weekend', Calculations.isWeekend(sunday), true);
  verifier.verify('Monday is Not Weekend', Calculations.isWeekend(new Date('2025-08-18')), false);
  
  // Test 2: Past Date Detection
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  verifier.verify('Yesterday is Past', Calculations.isPastDate(yesterday), true);
  verifier.verify('Tomorrow is Not Past', Calculations.isPastDate(tomorrow), false);
  verifier.verify('Today is Not Past', Calculations.isPastDate(new Date()), false);
  
  // Test 3: Trading Window for Past Dates
  const pastDate = new Date('2025-01-01');
  const pastWindow = Calculations.tradingWindow(pastDate, '16:00');
  verifier.verify('Past Date Trading Window', pastWindow, 'Past');
  
  // Test 4: Currency Formatting with Large Numbers
  const largeAmount = 10000000; // 10 million
  const formattedLarge = Calculations.formatCurrency(largeAmount);
  verifier.verify('Large Currency Format', formattedLarge, '$10,000,000');
  
  const smallAmount = 0.49;
  const formattedSmall = Calculations.formatCurrency(smallAmount);
  verifier.verify('Small Currency Rounds', formattedSmall, '$0');
  
  // Test 5: Percentage Formatting Edge Cases
  const zeroPercent = Calculations.formatPercentage(0, 1);
  verifier.verify('Zero Percentage', zeroPercent, '0.0%');
  
  const negativePercent = Calculations.formatPercentage(-5.5, 1);
  verifier.verify('Negative Percentage', negativePercent, '-5.5%');
  
  const largePercent = Calculations.formatPercentage(150.789, 2);
  verifier.verify('Large Percentage', largePercent, '150.79%');
  
  // Test 6: Delta Formatting Edge Cases
  const negativeDelta = Calculations.formatDelta(-0.25);
  verifier.verify('Negative Delta Format', negativeDelta, 'Δ25');
  
  const smallDelta = Calculations.formatDelta(0.001);
  verifier.verify('Small Delta Rounds', smallDelta, 'Δ0');
  
  const largeDelta = Calculations.formatDelta(0.999);
  verifier.verify('Large Delta Rounds', largeDelta, 'Δ100');
  
  // Test 7: Strike Distance with Extreme Values
  const veryHighStrike = 10000;
  const currentPrice = 636.83;
  const extremeDistance = Calculations.strikeDistance(veryHighStrike, currentPrice);
  verifier.verify('Extreme Strike Distance', 
    extremeDistance.formatted, 
    '+9363.17 (1470.0%)'
  );
  
  // Test 8: Days to Expiration Edge Cases
  const farFuture = new Date('2026-12-31');
  const daysToFarFuture = Calculations.daysToExpiration(farFuture);
  verifier.verify('Far Future Days > 365', daysToFarFuture > 365, true);
  
  // Test 9: Date Formatting Edge Cases
  const newYear = new Date('2025-01-01');
  const formattedNewYear = Calculations.formatDate(newYear);
  verifier.verify('New Year Date Format', formattedNewYear, '01/01/2025');
  
  const leapDay = new Date('2024-02-29');
  const formattedLeapDay = Calculations.formatDate(leapDay);
  verifier.verify('Leap Day Format', formattedLeapDay, '02/29/2024');
  
  // Test 10: Trading Window Across DST
  // Note: This is a simplified test - full DST testing would be more complex
  const dstDate = new Date('2025-03-09'); // DST starts March 9, 2025
  const dstWindow = Calculations.tradingWindow(dstDate, '16:00');
  // Just verify it doesn't crash and returns a valid format
  const isValidFormat = /^\d+[dhm]/.test(dstWindow) || dstWindow === 'Past';
  verifier.verify('DST Date Handling', isValidFormat, true);
  
  // Log summary
  const summary = verifier.getSummary();
  console.log(`Edge Case Tests Complete: ${summary.passed}/${summary.total} passed`);
  console.groupEnd();
  
  return summary;
}

// Export for use in components
export default runEdgeCaseTests;