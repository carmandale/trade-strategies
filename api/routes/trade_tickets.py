from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date, datetime
from decimal import Decimal
import yfinance as yf

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


Action = Literal["BUY", "SELL"]
OptionType = Literal["CALL", "PUT"]
Side = Literal["DEBIT", "CREDIT"]
TIF = Literal["DAY", "GTC"]


class OptionLeg(BaseModel):
    action: Action
    type: OptionType
    strike: float
    expiration: date
    quantity: int = Field(1, ge=1)


class Pricing(BaseModel):
    side: Side
    net: Decimal
    limit: Optional[Decimal] = None
    tif: TIF = "GTC"


class TicketRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    strategy_type: Optional[str] = None
    contracts: int = Field(1, gt=0)
    legs: List[OptionLeg]
    pricing: Pricing
    notes: Optional[str] = None


class TicketResponse(BaseModel):
    symbol: str
    strategy_type: Optional[str]
    contracts: int
    legs: List[OptionLeg]
    pricing: Pricing
    underlying_price: Optional[float]
    timestamp: str
    fidelity_fields: List[dict]
    copy_text: str


def _mmddyyyy(d: date) -> str:
    return d.strftime("%m/%d/%Y")


def _fetch_underlying_price(symbol: str) -> Optional[float]:
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="1d", interval="1m")
        if hist is not None and not hist.empty:
            return float(hist["Close"].iloc[-1])
        hist = t.history(period="5d", interval="1d")
        if hist is not None and not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None


@router.post("/options-multileg", response_model=TicketResponse)
async def create_options_multileg_ticket(req: TicketRequest):
    try:
        symbol = req.symbol.upper()
        now_iso = datetime.utcnow().isoformat()
        price = _fetch_underlying_price(symbol)

        # Fidelity-oriented row mapping per leg
        rows: List[dict] = []
        for leg in req.legs:
            rows.append({
                "Action": leg.action,
                "Qty": leg.quantity * req.contracts,
                "Symbol": symbol,
                "Expiration": _mmddyyyy(leg.expiration),
                "Strike": f"{leg.strike:.2f}",
                "Type": leg.type,
            })

        price_label = "Net Debit" if req.pricing.side == "DEBIT" else "Net Credit"
        limit_str = f" Limit {req.pricing.limit}" if req.pricing.limit is not None else ""

        # Plain text copy block
        lines = [
            f"Options Multi-Leg Ticket for {symbol}",
            f"{price_label}: {req.pricing.net}{limit_str}  TIF: {req.pricing.tif}",
            "Legs:",
        ]
        for r in rows:
            lines.append(
                f"- {r['Action']} {r['Qty']} {r['Symbol']} {r['Expiration']} {r['Strike']} {r['Type']}"
            )
        if req.notes:
            lines.append(f"Notes: {req.notes}")

        return TicketResponse(
            symbol=symbol,
            strategy_type=req.strategy_type,
            contracts=req.contracts,
            legs=req.legs,
            pricing=req.pricing,
            underlying_price=price,
            timestamp=now_iso,
            fidelity_fields=rows,
            copy_text="\n".join(lines),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



