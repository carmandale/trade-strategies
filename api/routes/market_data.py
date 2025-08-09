from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta, timezone
import yfinance as yf
from sqlalchemy.orm import Session
from database.config import get_db
from database.models import MarketDataCache

router = APIRouter(tags=["market_data"])

CURRENT_PRICE_TTL_SECONDS = 60
HISTORICAL_TTL_SECONDS = 300


@router.get("/current_price/{symbol}")
async def get_current_price(symbol: str, db: Session = Depends(get_db)):
    try:
        symbol = symbol.upper()
        now = datetime.now(timezone.utc)

        # Try cache (latest non-expired entry)
        cached = (
            db.query(MarketDataCache)
            .filter(
                MarketDataCache.symbol == symbol,
                MarketDataCache.data_type == "current_price",
                MarketDataCache.expires_at > now,
            )
            .order_by(MarketDataCache.data_date.desc())
            .first()
        )
        if cached:
            data = cached.data
            return {"symbol": symbol, "price": float(data["price"]), "timestamp": data["timestamp"]}

        # Fetch fresh
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        price = None
        ts = None
        if hist is not None and not hist.empty:
            last = hist.tail(1)
            price = float(last["Close"].iloc[0])
            ts = last.index[-1].to_pydatetime().isoformat()
        else:
            dailies = ticker.history(period="5d", interval="1d")
            if dailies is not None and not dailies.empty:
                last = dailies.tail(1)
                price = float(last["Close"].iloc[0])
                ts = last.index[-1].to_pydatetime().isoformat()

        if price is None:
            raise HTTPException(status_code=404, detail=f"No price data for {symbol}")

        # Store in cache
        entry = MarketDataCache(
            symbol=symbol,
            data_date=now,
            data_type="current_price",
            data={"price": price, "timestamp": ts or now.isoformat()},
            expires_at=now + timedelta(seconds=CURRENT_PRICE_TTL_SECONDS),
        )
        db.add(entry)
        db.commit()

        return {"symbol": symbol, "price": price, "timestamp": ts or now.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical_data/{symbol}")
async def get_historical_data(
    symbol: str,
    period: str = Query("1d"),
    interval: str = Query("1m"),
    db: Session = Depends(get_db),
):
    try:
        symbol = symbol.upper()
        now = datetime.now(timezone.utc)
        cache_key = f"historical:{period}:{interval}"

        cached = (
            db.query(MarketDataCache)
            .filter(
                MarketDataCache.symbol == symbol,
                MarketDataCache.data_type == cache_key,
                MarketDataCache.expires_at > now,
            )
            .order_by(MarketDataCache.data_date.desc())
            .first()
        )
        if cached:
            return {"symbol": symbol, "data": cached.data}

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

        # Cache
        entry = MarketDataCache(
            symbol=symbol,
            data_date=now,
            data_type=cache_key,
            data=data,
            expires_at=now + timedelta(seconds=HISTORICAL_TTL_SECONDS),
        )
        db.add(entry)
        db.commit()

        return {"symbol": symbol, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



