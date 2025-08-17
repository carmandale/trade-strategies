# SPX vs SPY Analysis Report

**Date:** August 17, 2025  
**Purpose:** Clarify and align on SPX vs SPY usage throughout the application

## Executive Summary

You are correct - there IS inconsistency between SPX and SPY usage throughout the application. The codebase shows a mixed usage pattern that needs alignment.

## Evidence-Based Analysis

### 1. Backend Python Scripts (Original Implementation)

**ALL legacy scripts use SPX data:**

```python
# daily/daily.py (line 3, 52)
# Historical daily SPX closes for Jul 16-29, 2024
print("Backtest Results for Daily (0DTE) Iron Condors on SPX")

# weekly/weekly.py (line 3)
# Historical Friday SPX closes

# monthly/monthly.py
# Similar SPX usage pattern

# backtest_strategies.py (lines 20-22, 84)
ticker = '^GSPC'  # This is SPX index in yfinance
print(f"Backtest Results for {self.timeframe.capitalize()} Iron Condors on SPX")
```

**SPX price ranges in data:**
- Daily data shows: 5399.22 - 5631.22 (July 2024)
- These are SPX index values (~5400-5600 range)

### 2. Frontend React/TypeScript

**Predominantly uses SPY:**

```typescript
// src/services/marketApi.ts (lines 86, 89)
'SPY': 430.50,  // SPY ETF price
'SPX': 4305.20, // SPX index price (10x SPY approximately)

// src/services/strategyApi.ts (lines 286-303)
name: 'SPY Iron Condor Daily',
symbol: 'SPY',

// src/services/api.ts (lines 117-118, 140)
static async getCurrentPrice(ticker: string = 'SPY'): Promise<number>

// src/App.tsx (lines 3-4, 26, 28)
import SPYSpreadStrategiesApp from './components/generated/SPYSpreadStrategiesApp';
import ConsolidatedSPYApp from './components/ConsolidatedSPYApp';
```

### 3. API Layer

**Mixed usage with defaults to different symbols:**

```python
# api/routes/ai_assessment.py (line 25)
symbol: str = Field(default="SPX", description="Trading symbol")

# scripts/migrate_data.py (line 29)
self.default_symbol = "SPY"  # Default symbol for legacy trades

# tests/test_api_endpoints.py (multiple lines)
"symbol": "SPY"  # All test cases use SPY
```

### 4. New IB Integration Spec

**I created the Phase 2 spec focusing on SPX:**

```markdown
# From spec.md (lines 16, 30, 44)
- "Real-time bid/ask spreads and last prices for SPX options"
- "User connects to IB Gateway, subscribes to SPX options data"
- "Multi-symbol support beyond SPX (Phase 2 focuses on SPX only)"
```

## Key Differences Between SPX and SPY

| Aspect | SPX (S&P 500 Index) | SPY (SPDR S&P 500 ETF) |
|--------|---------------------|------------------------|
| **Type** | Cash-settled index | Tradeable ETF |
| **Price Range** | ~4300-5600 | ~430-560 |
| **Options Style** | European (exercise at expiration only) | American (exercise anytime) |
| **Settlement** | Cash | Shares |
| **Contract Size** | $100 x index value | 100 shares |
| **Trading Hours** | Index hours + some extended | Regular + extended ETF hours |
| **Tax Treatment** | 60/40 long/short term gains | Standard equity treatment |
| **Options Liquidity** | Very high (institutional) | Extremely high (retail + institutional) |
| **Strike Intervals** | 5-point increments | 1-point increments |
| **Interactive Brokers Symbol** | SPX | SPY |

## Implications for Iron Condor Strategies

### SPX Advantages:
1. **Cash settlement** - No assignment risk, cleaner P&L
2. **European style** - No early assignment concerns
3. **Tax benefits** - 60/40 treatment for US traders
4. **Larger notional** - Fewer contracts needed
5. **Professional focus** - Your strike rounding logic (nearest 5) matches SPX

### SPY Advantages:
1. **Smaller capital requirements** - 1/10th the size
2. **Tighter spreads** - More retail participation
3. **More strike choices** - 1-point increments
4. **Easier to test** - Smaller positions for paper trading
5. **More accessible** - Better for retail traders

## Recommendation

**I recommend standardizing on SPX for the following reasons:**

1. **Original Intent**: All your backtesting scripts use SPX data
2. **Strike Logic**: Your "round to nearest 5" logic matches SPX conventions
3. **Professional Trading**: SPX is the standard for institutional Iron Condor strategies
4. **IB Integration**: SPX options are well-supported on Interactive Brokers
5. **Cash Settlement**: Eliminates assignment risk for Iron Condors
6. **Tax Efficiency**: Better tax treatment for profitable strategies

## Required Changes for SPX Standardization

### Backend Changes:
- ✅ Already using SPX in legacy scripts
- ✅ AI assessment defaults to SPX
- ⚠️ Need to update migration script default from SPY to SPX
- ⚠️ Need to update test cases from SPY to SPX

### Frontend Changes:
- ⚠️ Rename components from "SPYSpreadStrategiesApp" to "SPXSpreadStrategiesApp"
- ⚠️ Update marketApi.ts to use SPX as primary symbol
- ⚠️ Update strategyApi.ts mock data to use SPX
- ⚠️ Update default symbol in api.ts from SPY to SPX
- ⚠️ Adjust price displays to handle 4-digit SPX prices

### Database/Model Changes:
- ⚠️ Update any SPY references in database seeds
- ⚠️ Ensure models support both but default to SPX

### UI/UX Considerations:
- ⚠️ Update labels to show "SPX" instead of "SPY"
- ⚠️ Adjust number formatting for larger SPX values
- ⚠️ Update strike selection to show 5-point increments

## Alternative: Support Both

We could also support BOTH SPX and SPY with a toggle:
- Let users choose their preferred underlying
- Adjust strike increments dynamically (5 for SPX, 1 for SPY)
- Scale position sizing appropriately
- Store preference in user settings

## Decision Required

**Please confirm which approach you prefer:**

1. **Option A: Standardize on SPX** (Recommended)
   - Aligns with original backtesting code
   - Professional trading focus
   - Cleaner for Iron Condors

2. **Option B: Standardize on SPY**
   - More accessible for retail traders
   - Smaller capital requirements
   - Tighter spreads

3. **Option C: Support Both**
   - Maximum flexibility
   - More complex implementation
   - User choice

Once you confirm, I can:
- Update the Phase 2 spec if needed
- Create tasks to standardize the codebase
- Ensure IB integration uses the correct symbol