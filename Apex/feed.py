import time
import requests
import random
from datetime import datetime

KRAKEN_API = "https://api.kraken.com/0/public"

PAIRS = {
    "BTC/USD": "XBTUSD",
    "ETH/USD": "ETHUSD",
    "SOL/USD": "SOLUSD",
    "XRP/USD": "XRPUSD",
    "ADA/USD": "ADAUSD",
}

def get_price(symbol: str) -> float | None:
    """Get current price from Kraken."""
    kraken_pair = PAIRS.get(symbol)
    if not kraken_pair:
        return None
    try:
        r = requests.get(f"{KRAKEN_API}/Ticker", params={"pair": kraken_pair}, timeout=5)
        data = r.json()
        if data.get("error"):
            return None
        result = data.get("result", {})
        for key, val in result.items():
            return float(val["c"][0])
    except Exception:
        return None

def get_ohlcv(symbol: str, interval: int = 5, limit: int = 100) -> list[dict]:
    """
    Get OHLCV candles from Kraken.
    interval in minutes: 1, 5, 15, 30, 60, 240, 1440
    Returns list of dicts with keys: time, open, high, low, close, volume
    """
    kraken_pair = PAIRS.get(symbol)
    if not kraken_pair:
        return _synthetic_ohlcv(symbol, limit)
    try:
        r = requests.get(
            f"{KRAKEN_API}/OHLC",
            params={"pair": kraken_pair, "interval": interval},
            timeout=10
        )
        data = r.json()
        if data.get("error"):
            return _synthetic_ohlcv(symbol, limit)
        result = data.get("result", {})
        candles = []
        for key, rows in result.items():
            if key == "last":
                continue
            for row in rows[-limit:]:
                candles.append({
                    "time":   int(row[0]),
                    "open":   float(row[1]),
                    "high":   float(row[2]),
                    "low":    float(row[3]),
                    "close":  float(row[4]),
                    "volume": float(row[6]),
                })
        return candles
    except Exception:
        return _synthetic_ohlcv(symbol, limit)

def _synthetic_ohlcv(symbol: str, limit: int = 100) -> list[dict]:
    """Fallback synthetic candles if Kraken is unreachable."""
    base_prices = {
        "BTC/USD": 65000, "ETH/USD": 3500,
        "SOL/USD": 150,   "XRP/USD": 0.55, "ADA/USD": 0.45,
    }
    price = base_prices.get(symbol, 100)
    now = int(time.time()) // 300 * 300
    candles = []
    for i in range(limit):
        t = now - (limit - i) * 300
        change = random.uniform(-0.005, 0.005)
        o = price
        c = price * (1 + change)
        h = max(o, c) * random.uniform(1.0, 1.003)
        l = min(o, c) * random.uniform(0.997, 1.0)
        candles.append({"time": t, "open": o, "high": h, "low": l, "close": c, "volume": random.uniform(1, 50)})
        price = c
    return candles

def get_all_prices() -> dict:
    """Returns current prices for all pairs."""
    prices = {}
    for symbol in PAIRS:
        p = get_price(symbol)
        if p:
            prices[symbol] = p
    return prices
get_candles = get_ohlcv  # alias para compatibilidad con main.py
