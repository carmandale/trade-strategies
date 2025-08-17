# SPX Standardization Tasks

**Created:** 2025-08-17  
**Purpose:** Complete list of changes to standardize the application on SPX (S&P 500 Index) instead of SPY

## Summary

Standardizing the entire application to use SPX exclusively for consistency with the original backtesting logic and professional trading practices.

## Frontend Changes

### Component Renaming
- [ ] Rename `SPYSpreadStrategiesApp.tsx` → `SPXSpreadStrategiesApp.tsx`
- [ ] Rename `ConsolidatedSPYApp.tsx` → `ConsolidatedSPXApp.tsx`
- [ ] Update all imports in `App.tsx` to use new component names
- [ ] Update component display names and titles

### Service Layer Updates

#### src/services/marketApi.ts
- [ ] Change default symbol from 'SPY' to 'SPX'
- [ ] Update mock price from 430.50 to 4305.20 (keep SPX at correct level)
- [ ] Remove SPY from basePrices, keep only SPX

#### src/services/strategyApi.ts
- [ ] Change all 'SPY' references to 'SPX' in mock strategies
- [ ] Update strategy names from "SPY Iron Condor" to "SPX Iron Condor"
- [ ] Update symbol field from 'SPY' to 'SPX'
- [ ] Adjust strike prices to SPX scale (multiply by 10)

#### src/services/api.ts
- [ ] Change default ticker from 'SPY' to 'SPX'
- [ ] Update getCurrentPrice default parameter
- [ ] Update all method signatures using SPY

### UI Text Updates
- [ ] Change "Current SPY:" to "Current SPX:" in headers
- [ ] Update all user-facing text mentioning SPY
- [ ] Adjust number formatting for 4-digit SPX prices
- [ ] Update tooltips and help text

### Test Updates
- [ ] Update all frontend test files replacing SPY with SPX
- [ ] Adjust test price expectations (430 → 4300 range)
- [ ] Update test selectors looking for SPY text

## Backend Changes

### API Route Updates

#### api/routes/market.py
- [ ] Ensure yfinance uses '^GSPC' for SPX (already correct)
- [ ] Update any SPY references in route documentation

#### api/routes/strategies.py
- [ ] Update default symbol parameters to SPX
- [ ] Verify strike rounding uses 5-point increments

#### api/routes/ai_assessment.py
- [ ] ✅ Already defaults to SPX (no change needed)

### Database/Migration Updates

#### scripts/migrate_data.py
- [ ] Change `self.default_symbol = "SPY"` to `"SPX"`
- [ ] Update migration logic to use SPX for legacy trades

#### Database Seeds
- [ ] Update any seed data using SPY to use SPX
- [ ] Adjust strike prices in seed data to SPX scale

### Test Suite Updates

#### tests/test_api_endpoints.py
- [ ] Replace all "SPY" with "SPX" in test payloads
- [ ] Update expected response assertions
- [ ] Adjust price ranges in tests

#### tests/test_ib_strategy_calculations.py
- [ ] Change symbol from 'SPY' to 'SPX'
- [ ] Update strike prices (440 → 4400, etc.)
- [ ] Verify calculations work with SPX scale

## Configuration Updates

### Environment Variables
- [ ] Add SPX-specific configuration if needed
- [ ] Document SPX as the standard symbol

### Documentation Updates
- [ ] Update CLAUDE.md to clarify SPX usage
- [ ] Update README.md if it mentions SPY
- [ ] Update any API documentation

## Interactive Brokers Integration

### Market Data Service
- [ ] Ensure IBMarketDataService requests SPX options
- [ ] Verify contract specifications for SPX index options
- [ ] Test with actual SPX symbols on IB Gateway

### WebSocket Streaming
- [ ] Configure WebSocket to stream SPX data
- [ ] Update subscription management for SPX

## Validation Checklist

### Strike Price Logic
- [ ] Verify round_to_5() function works correctly for SPX
- [ ] Ensure strike selection percentages appropriate for SPX
- [ ] Test Iron Condor strikes at SPX scale

### Price Display
- [ ] Format SPX prices correctly (4300.00 format)
- [ ] Handle percentage calculations based on SPX values
- [ ] Ensure P/L calculations scale correctly

### Historical Data
- [ ] Verify yfinance fetches SPX (^GSPC) correctly
- [ ] Ensure historical backtesting uses SPX data
- [ ] Validate date ranges have SPX data available

## Testing Plan

1. **Unit Tests**: Update and run all unit tests with SPX values
2. **Integration Tests**: Test API endpoints with SPX symbols
3. **E2E Tests**: Verify UI displays SPX correctly
4. **Manual Testing**: 
   - Test strategy creation with SPX
   - Verify strike selection at SPX scale
   - Confirm P/L calculations accurate

## Rollout Strategy

1. **Phase 1**: Update backend first (API, tests, database)
2. **Phase 2**: Update frontend services and components
3. **Phase 3**: Update UI text and formatting
4. **Phase 4**: Full testing and validation
5. **Phase 5**: Deploy and monitor

## Notes

- SPX trades at approximately 10x SPY values
- SPX options have 5-point strike increments
- SPX options are European-style (exercise at expiration only)
- SPX options are cash-settled
- Tax treatment: 60% long-term, 40% short-term gains

## Success Criteria

- [ ] All tests pass with SPX values
- [ ] No SPY references remain in active code
- [ ] UI correctly displays SPX prices and strikes
- [ ] IB integration works with SPX options
- [ ] Backtesting results consistent with original scripts