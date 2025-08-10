# Product Roadmap

> Last Updated: 2025-08-10
> Version: 1.0.2
> Status: Active Development

## Phase 0: Already Completed

The following features have been implemented:

- [x] **Iron Condor Backtesting Framework** - Complete Python backtesting system for Iron Condor strategies `L`
- [x] **Multi-Timeframe Analysis** - Daily (0DTE), weekly, and monthly strategy backtesting `M`
- [x] **Strike Selection Logic** - Percentage-based strike selection with 5-point rounding `S`
- [x] **Historical Data Integration** - yfinance integration for SPX historical data `M`
- [x] **P/L Calculation Engine** - Accurate profit/loss calculations for options spreads `M`
- [x] **Command-Line Interface** - Configurable backtesting with adjustable parameters `S`
- [x] **Performance Metrics** - Win rate, total P/L, Sharpe ratio, and drawdown analysis `M`
- [x] **Chart Generation** - Matplotlib-based equity curves and P/L histograms `S`
- [x] **React Frontend Foundation** - Professional React 19 + TypeScript + Tailwind CSS + Framer Motion setup `L`
- [x] **Trading Interface Components** - Complete UI components for options strategy configuration `M`
- [x] **API Service Integration** - Frontend-backend communication layer with fallback handling `M`
- [x] **uv-only & Postgres-only Standardization** - Project uses `uv` for Python and PostgreSQL exclusively for the backend database
- [x] **Test Infrastructure Setup** - Vitest for unit/integration tests, Playwright for E2E testing `M`

## Current Work In Progress

### Issue #10: Frontend Test Fixes
**Status:** Active - Fixing test failures
**Goal:** Achieve 100% test pass rate across all test suites

- [ ] **Accessibility Improvements** - Add proper ARIA attributes for tabs and panels `S`
- [ ] **Test Selector Fixes** - Add data-testid attributes to components for reliable test queries `S`
- [ ] **Duplicate Text Cleanup** - Fix duplicate timeframe labels with aria-hidden `S`
- [ ] **Tab Role Implementation** - Proper tablist/tab/tabpanel structure for strategy selection `M`

**Target Results:**
- Backend Tests: ✅ 118/118 (already passing)
- Frontend Vitest: 72/72 (currently 50/72)
- E2E Playwright: 22/22 (currently 4/22)

## Phase 1: Web Application Foundation (2 weeks)

**Goal:** Transform existing Python scripts into a web-based application
**Success Criteria:** Working React frontend with FastAPI backend serving existing backtesting functionality

### Must-Have Features

- [ ] FastAPI Backend Setup - Migrate existing backtesting logic to REST API endpoints `L`
- [x] React Frontend Bootstrap - Create responsive UI with Tailwind CSS and shadcn/ui `L`
- [x] Database Schema Design - PostgreSQL setup for storing strategies and backtest results `M`
- [ ] Basic Strategy Display - Show existing Iron Condor results in web interface `M`
- [ ] Real-Time Data Pipeline - Replace hardcoded data with live yfinance integration `L`

### Should-Have Features

- [ ] User Authentication - Simple login system for single-user application `M`
- [ ] Strategy History - Store and retrieve previous backtest runs `S`

### Dependencies

- Project structure setup (monorepo)
- Environment configuration files
- Database migrations (Alembic, PostgreSQL)

## Phase 2: Interactive Strategy Configuration (2 weeks)

**Goal:** Enable real-time strategy configuration with visual feedback
**Success Criteria:** Users can adjust strategy parameters and see immediate backtesting results

### Must-Have Features

- [ ] Interactive Strike Selection - Visual controls for adjusting put/call strike percentages `L`
- [ ] Real-Time Backtesting - Instant results when parameters change `L`
- [ ] Strategy Parameter UI - Intuitive controls for credit, timeframe, and position sizing `M`
- [ ] Visual P/L Display - Charts showing profit/loss profiles and risk metrics `L`
- [ ] Multi-Strategy Comparison - Side-by-side comparison of daily, weekly, monthly strategies `M`

### Should-Have Features

- [ ] Strategy Templates - Predefined configurations for common setups `S`
- [ ] Performance Alerts - Notifications when strategies hit performance thresholds `S`

### Dependencies

- Phase 1 completion
- Chart library integration
- Real-time data feeds

## Phase 3: Market Sentiment Integration (1 week)

**Goal:** Add real-time market sentiment analysis to enhance strategy generation
**Success Criteria:** System generates three strategies based on current market conditions

### Must-Have Features

- [ ] Market Sentiment API - Integration with news/social sentiment data sources `L`
- [ ] Volatility Analysis - Real-time VIX and implied volatility integration `M`
- [ ] Strategy Recommendation Engine - Algorithm that suggests optimal strategies based on sentiment `L`
- [ ] Sentiment Dashboard - Visual display of current market sentiment metrics `M`

### Should-Have Features

- [ ] Sentiment History - Track sentiment trends over time `S`
- [ ] Custom Sentiment Weights - Allow user to adjust sentiment factors `S`

### Dependencies

- External API integrations (Alpha Vantage, news APIs)
- Advanced analytics implementation

## Phase 4: Advanced Visualization & Strategy Types (1 week)

**Goal:** Expand strategy types and enhance visualization capabilities
**Success Criteria:** Support for Bull Call Spreads, enhanced charts, and strategy analytics

### Must-Have Features

- [ ] Bull Call Spread Implementation - Add directional strategy support `M`
- [ ] Advanced Charting - Interactive TradingView-style charts `L`
- [ ] Risk Visualization - Greeks display and risk parameter analysis `M`
- [ ] Strategy Performance Analytics - Enhanced metrics and performance tracking `M`

### Should-Have Features

- [ ] Custom Strategy Builder - Allow users to create custom options strategies `L`
- [ ] Export Functionality - Export strategies and results to CSV/PDF `S`

### Dependencies

- TradingView charting library integration
- Options Greeks calculations

## Phase 5: Production Optimization (3 days)

**Goal:** Optimize for production deployment and user experience
**Success Criteria:** Fast, reliable application ready for daily trading use

### Must-Have Features

- [ ] Performance Optimization - Sub-second response times for backtesting `M`
- [ ] Error Handling - Robust error handling for API failures and data issues `S`
- [ ] Deployment Pipeline - Automated deployment to Vercel/Railway `S`
- [ ] Data Caching - Redis caching for frequently accessed market data `M`

### Should-Have Features

- [ ] Mobile Responsive Design - Ensure usability on tablets and phones `M`
- [ ] Offline Mode - Basic functionality when market data is unavailable `S`

### Dependencies

- Production hosting setup
- Performance monitoring tools
- CI/CD pipeline configuration