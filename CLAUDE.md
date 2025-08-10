# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md
- **Decision History:** @.agent-os/product/decisions.md

### Development Standards
- **Code Style:** @~/.agent-os/standards/code-style.md
- **Best Practices:** @~/.agent-os/standards/best-practices.md

### Project Management
- **Active Specs:** @.agent-os/specs/
- **Spec Planning:** Use `@~/.agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/.agent-os/instructions/execute-tasks.md`

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @.agent-os/instructions/create-spec.md
   - For tasks execution: @.agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- Product-specific files in `.agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `.agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above.

## Legacy Codebase Overview

The repository originally included a standalone root FastAPI app (`main.py`) with a `/analyze` endpoint, a `static/index.html`, and file-based `trades.json`. These have been removed in favor of the database‑backed API under `api/` and React frontend in `src/`.

Historical prototype scripts are organized by timeframe:

- **`daily/`** – 0DTE prototypes
- **`monthly/`** – monthly expiration prototypes
- **`weekly/`** – weekly prototypes

## Core Strategy: Iron Condor

The existing codebase implements backtesting for Iron Condor options strategies, which involve:
1. Selling a put spread below the current price
2. Selling a call spread above the current price
3. Collecting premium with the goal that price stays within the range

## Key Implementation Details

### Strike Selection Logic
Scripts use a percentage-based approach for strike selection:
- **Daily (0DTE)**: Put spread: 97.5% / 98%, Call spread: 102% / 102.5%
- **Monthly**: Put spread: 94% / 95%, Call spread: 105% / 106%
- **Weekly**: Put spread: 96.5% / 97%, Call spread: 103% / 103.5%

### Common Patterns
- Strikes rounded to nearest 5 points using `round_to_5()` function
- P/L calculations account for spread values at expiration
- Fixed credit assumptions vary by timeframe

## Legacy Scripts

Reference-only utilities are kept for exploration. Use `api/main.py` as the canonical API; do not rely on the removed root `main.py` or `/analyze`.

```bash
# Example legacy backtester (reference only)
python backtest_strategies.py --timeframe daily --plot --export
```