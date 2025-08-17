# Issue #42: Fix Pre-existing Test Failures

## Tasks

- [x] 1. Fix IB Connection API Test Failures
  - [x] 1.1 Fix mock return types for connection manager
  - [x] 1.2 Update test assertions for dictionary responses
  - [x] 1.3 Fix health endpoint status code (503 when unhealthy)
  - [x] 1.4 Verify all IB connection tests pass

- [x] 2. Fix Database Connection Issues
  - [x] 2.1 Update conftest.py with comprehensive mocking
  - [x] 2.2 Switch from Docker PostgreSQL to SQLite for tests
  - [x] 2.3 Add smart mock behaviors for ORM operations
  - [x] 2.4 Fix Strategy model test with explicit fields

- [ ] 3. Fix Remaining Model Tests
  - [ ] 3.1 Fix Backtest model tests
  - [ ] 3.2 Fix Trade model tests  
  - [ ] 3.3 Fix MarketDataCache model tests
  - [ ] 3.4 Fix model constraint tests
  - [ ] 3.5 Fix foreign key relationship tests

- [ ] 4. Fix Market Data Service Tests
  - [ ] 4.1 Fix get_current_spx_price test
  - [ ] 4.2 Fix collect_market_snapshot test
  - [ ] 4.3 Fix save_market_snapshot test
  - [ ] 4.4 Fix cached snapshot test
  - [ ] 4.5 Fix error handling tests

- [ ] 5. Fix Schema Validation Tests
  - [ ] 5.1 Fix default values test
  - [ ] 5.2 Fix JSONB field tests
  - [ ] 5.3 Fix enum constraint tests

- [ ] 6. Fix IB Market Data Tests
  - [ ] 6.1 Fix options chain tests
  - [ ] 6.2 Fix Greeks calculation tests
  - [ ] 6.3 Fix streaming tests
  - [ ] 6.4 Fix rate limiting tests

## Progress Summary
- Initial failures: 118+ 
- After Task 1: ~89 failures
- After Task 2: 83 failures
- Current status: Tasks 1-2 complete, working on Task 3