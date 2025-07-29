from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from ta import momentum, volatility, trend

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

class SpreadAnalysisRequest(BaseModel):
    date: str
    ticker: str = "SPY"
    contracts: int = 200
    bull_call_strikes: List[float]
    iron_condor_strikes: List[float]
    butterfly_strikes: List[float]
    entry_time: str = "08:30:00"
    exit_time: str = "14:30:00"

class TradeEntry(BaseModel):
    date: str
    strategy: str
    strikes: List[float]
    contracts: int
    entry_price: float
    credit_debit: float
    notes: Optional[str] = ""

def get_spy_data(date: str, ticker: str = "SPY"):
    """Fetch intraday data for given date"""
    try:
        data = yf.download(ticker, start=date, 
                         end=(datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"), 
                         interval="1m", progress=False)
        if data.empty:
            # Try 5-minute intervals if 1-minute fails
            data = yf.download(ticker, start=date, 
                             end=(datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"), 
                             interval="5m", progress=False)
        
        # Convert timezone
        if not data.empty:
            data.index = data.index.tz_convert('America/Chicago')
        
        # Flatten column names if MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching data: {str(e)}")

def calculate_indicators(data):
    """Calculate technical indicators"""
    # Ensure we have a proper Series for Close prices
    if 'Close' not in data.columns:
        raise ValueError("No 'Close' column in data")
    
    close_series = data['Close']
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()
    
    # Only calculate indicators if we have enough data
    if len(close_series) < 20:
        # Return data without indicators if not enough points
        data['BB_Mid'] = close_series
        data['BB_Upper'] = close_series
        data['BB_Lower'] = close_series
        data['RSI'] = 50.0  # Neutral RSI
        data['MACD'] = 0.0
        data['MACD_Signal'] = 0.0
    else:
        bb = volatility.BollingerBands(close=close_series, window=20, window_dev=2)
        data['BB_Mid'] = bb.bollinger_mavg()
        data['BB_Upper'] = bb.bollinger_hband()
        data['BB_Lower'] = bb.bollinger_lband()
        data['RSI'] = momentum.RSIIndicator(close=close_series, window=14).rsi()
        macd = trend.MACD(close=close_series)
        data['MACD'] = macd.macd()
        data['MACD_Signal'] = macd.macd_signal()
    
    return data

def calculate_spread_profit(data, spread_type, strikes, entry_time, exit_time, contracts=200):
    """Calculate spread profitability"""
    try:
        # Get entry and exit prices
        entry_timestamp = f"{data.index[0].strftime('%Y-%m-%d')} {entry_time}"
        exit_timestamp = f"{data.index[0].strftime('%Y-%m-%d')} {exit_time}" if exit_time else None
        
        # Find closest timestamps if exact ones don't exist
        entry_price = None
        exit_price = None
        
        if entry_timestamp in data.index:
            entry_price = float(data.loc[entry_timestamp, 'Close'])
        else:
            # Find closest time
            target_time = pd.Timestamp(entry_timestamp)
            closest_idx = data.index[data.index.searchsorted(target_time)]
            entry_price = float(data.loc[closest_idx, 'Close'])
            
        if exit_timestamp and exit_timestamp in data.index:
            exit_price = float(data.loc[exit_timestamp, 'Close'])
        elif exit_timestamp:
            # Find closest time
            target_time = pd.Timestamp(exit_timestamp)
            if target_time <= data.index[-1]:
                closest_idx = data.index[data.index.searchsorted(target_time)]
                exit_price = float(data.loc[closest_idx, 'Close'])
            else:
                exit_price = float(data.iloc[-1]['Close'])
        else:
            exit_price = float(data.iloc[-1]['Close'])
            
    except Exception as e:
        print(f"Error in calculate_spread_profit: {e}")
        return {"max_profit": 0, "max_loss": 0, "profit_at_exit": 0, "entry_price": 0, "exit_price": 0}
    
    if spread_type == "bull_call":
        debit = (strikes[1] - strikes[0]) * 0.3
        max_profit = (strikes[1] - strikes[0] - debit) * contracts * 100
        max_loss = debit * contracts * 100
        profit = max(0, min(exit_price - strikes[0], strikes[1] - strikes[0]) - debit) * contracts * 100
    elif spread_type == "iron_condor":
        credit = 0.4
        width = strikes[3] - strikes[2]
        max_profit = credit * contracts * 100
        max_loss = (width - credit) * contracts * 100
        profit = max_profit if strikes[0] < exit_price < strikes[1] else -max_loss
    elif spread_type == "butterfly":
        debit = 0.25
        width = strikes[2] - strikes[0]
        max_profit = (width / 2 - debit) * contracts * 100
        max_loss = debit * contracts * 100
        dist = abs(exit_price - strikes[1])
        profit = max(0, (width / 2 - dist - debit)) * contracts * 100
    
    return {
        "max_profit": max_profit,
        "max_loss": max_loss,
        "profit_at_exit": profit,
        "entry_price": entry_price,
        "exit_price": exit_price
    }

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/analyze")
async def analyze_spread(request: SpreadAnalysisRequest):
    """Analyze spread strategies for given parameters"""
    try:
        # Fetch and process data
        data = get_spy_data(request.date, request.ticker)
        data = calculate_indicators(data)
        
        # Get price data for charting
        chart_data = []
        for idx in range(0, len(data), 5):  # Sample every 5 minutes for performance
            row = data.iloc[idx]
            close_val = row['Close']
            if isinstance(close_val, pd.Series):
                close_val = close_val.iloc[0]
            
            chart_data.append({
                "time": row.name.strftime("%H:%M"),
                "price": float(close_val),
                "bb_upper": float(row['BB_Upper']) if 'BB_Upper' in row and not pd.isna(row['BB_Upper']) else None,
                "bb_lower": float(row['BB_Lower']) if 'BB_Lower' in row and not pd.isna(row['BB_Lower']) else None,
                "rsi": float(row['RSI']) if 'RSI' in row and not pd.isna(row['RSI']) else None
            })
        
        # Analyze each strategy
        results = {}
        results['bull_call'] = calculate_spread_profit(
            data, "bull_call", request.bull_call_strikes, 
            request.entry_time, request.exit_time, request.contracts
        )
        results['iron_condor'] = calculate_spread_profit(
            data, "iron_condor", request.iron_condor_strikes,
            request.entry_time, None, request.contracts
        )
        results['butterfly'] = calculate_spread_profit(
            data, "butterfly", request.butterfly_strikes,
            request.entry_time, request.exit_time, request.contracts
        )
        
        return {
            "date": request.date,
            "current_price": float(data.iloc[-1]['Close']) if isinstance(data.iloc[-1]['Close'], (int, float)) else float(data.iloc[-1]['Close'].iloc[0]),
            "chart_data": chart_data,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/current_price/{ticker}")
async def get_current_price(ticker: str = "SPY"):
    """Get current price for ticker"""
    try:
        spy = yf.Ticker(ticker)
        current_data = spy.history(period="1d", interval="1m")
        if not current_data.empty:
            return {"price": float(current_data['Close'].iloc[-1])}
        else:
            current_data = spy.history(period="1d")
            return {"price": float(current_data['Close'].iloc[-1])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Simple file-based storage for trades (for rapid prototyping)
TRADES_FILE = "trades.json"

def load_trades():
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trades(trades):
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f)

@app.post("/trades")
async def save_trade(trade: TradeEntry):
    """Save a trade entry"""
    trades = load_trades()
    trade_dict = trade.dict()
    trade_dict["id"] = len(trades) + 1
    trade_dict["timestamp"] = datetime.now().isoformat()
    trades.append(trade_dict)
    save_trades(trades)
    return trade_dict

@app.get("/trades")
async def get_trades():
    """Get all saved trades"""
    return load_trades()

@app.delete("/trades/{trade_id}")
async def delete_trade(trade_id: int):
    """Delete a trade"""
    trades = load_trades()
    trades = [t for t in trades if t.get("id") != trade_id]
    save_trades(trades)
    return {"message": "Trade deleted"}

if __name__ == "__main__":
    import uvicorn
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)