from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import yfinance as yf

router = APIRouter(tags=["market_data"])


@router.get("/current_price/{symbol}")
async def get_current_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        # Try to get the most recent 1m bar
        hist = ticker.history(period="1d", interval="1m")
        price = None
        ts = None
        if hist is not None and not hist.empty:
            last = hist.tail(1)
            price = float(last["Close"].iloc[0])
            ts = last.index[-1].to_pydatetime().isoformat()
        else:
            # Fallback to last daily close
            dailies = ticker.history(period="5d", interval="1d")
            if dailies is not None and not dailies.empty:
                last = dailies.tail(1)
                price = float(last["Close"].iloc[0])
                ts = last.index[-1].to_pydatetime().isoformat()

        if price is None:
            raise HTTPException(status_code=404, detail=f"No price data for {symbol}")

        return {"symbol": symbol.upper(), "price": price, "timestamp": ts or datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical_data/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = Query("1d"),
    interval: str = Query("1m"),
):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist is None or hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")

        data = []
        for idx, row in hist.iterrows():
            data.append({
                "timestamp": idx.to_pydatetime().isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if not isinstance(row["Volume"], float) else int(row["Volume"] or 0),
            })

        return {"symbol": symbol.upper(), "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



