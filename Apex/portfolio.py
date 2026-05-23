import uuid
import time
from datetime import datetime

INITIAL_CAPITAL  = 10_000.0   # USD
SIZE_PER_TRADE   = 100.0      # margin per trade
LEVERAGE         = 10         # 10x → $1000 notional
FEE_RATE         = 0.0005     # 0.05% per side
MAX_OPEN_TRADES  = 5

class Portfolio:
    def __init__(self):
        self.balance       = INITIAL_CAPITAL
        self.open_trades   = {}    # id → trade dict
        self.closed_trades = []    # list of closed trade dicts
        self.last_trade_time = {}  # symbol → timestamp

    # ── helpers ──────────────────────────────────────────────

    def _fee(self, notional: float) -> float:
        return round(notional * FEE_RATE, 4)

    def available_balance(self) -> float:
        used = sum(t["margin"] for t in self.open_trades.values())
        return round(self.balance - used, 4)

    def total_equity(self) -> float:
        """Balance + unrealized PnL of open trades (mark-to-market)."""
        unreal = sum(t.get("unrealized_pnl", 0) for t in self.open_trades.values())
        return round(self.balance + unreal, 4)

    # ── trade lifecycle ───────────────────────────────────────

    def can_open(self, symbol: str, cooldown_s: int = 120) -> bool:
        if len(self.open_trades) >= MAX_OPEN_TRADES:
            return False
        if self.available_balance() < SIZE_PER_TRADE:
            return False
        last = self.last_trade_time.get(symbol, 0)
        if time.time() - last < cooldown_s:
            return False
        return True

    def open_trade(self, symbol: str, direction: str,
                   entry_price: float, tp: float, sl: float) -> dict:
        notional = SIZE_PER_TRADE * LEVERAGE
        fee_open = self._fee(notional)
        trade = {
            "id":             str(uuid.uuid4())[:8],
            "symbol":         symbol,
            "direction":      direction,
            "entry_price":    entry_price,
            "tp":             tp,
            "sl":             sl,
            "margin":         SIZE_PER_TRADE,
            "notional":       notional,
            "fee_open":       fee_open,
            "open_time":      time.time(),
            "open_time_str":  datetime.utcnow().strftime("%H:%M:%S"),
            "unrealized_pnl": 0.0,
            "status":         "open",
        }
        self.open_trades[trade["id"]] = trade
        self.last_trade_time[symbol] = time.time()
        return trade

    def update_unrealized(self, trade_id: str, current_price: float):
        t = self.open_trades.get(trade_id)
        if not t:
            return
        if t["direction"] == "long":
            raw = (current_price - t["entry_price"]) / t["entry_price"] * t["notional"]
        else:
            raw = (t["entry_price"] - current_price) / t["entry_price"] * t["notional"]
        t["unrealized_pnl"] = round(raw, 4)
        t["current_price"]  = current_price

    def close_trade(self, trade_id: str, exit_price: float, reason: str) -> dict | None:
        t = self.open_trades.pop(trade_id, None)
        if not t:
            return None
        notional  = t["notional"]
        fee_close = self._fee(notional)
        if t["direction"] == "long":
            gross = (exit_price - t["entry_price"]) / t["entry_price"] * notional
        else:
            gross = (t["entry_price"] - exit_price) / t["entry_price"] * notional
        net_pnl = round(gross - t["fee_open"] - fee_close, 4)
        duration = round(time.time() - t["open_time"], 0)
        closed = {
            **t,
            "exit_price":     exit_price,
            "exit_time_str":  datetime.utcnow().strftime("%H:%M:%S"),
            "fee_close":      fee_close,
            "pnl":            net_pnl,
            "duration_s":     duration,
            "reason":         reason,
            "status":         "closed",
        }
        self.closed_trades.append(closed)
        self.balance = round(self.balance + net_pnl, 4)
        return closed

    def check_exits(self, current_prices: dict) -> list[dict]:
        """Check TP/SL for all open trades. Returns list of closed trades."""
        closed = []
        for tid, t in list(self.open_trades.items()):
            price = current_prices.get(t["symbol"])
            if not price:
                continue
            self.update_unrealized(tid, price)
            hit_tp = hit_sl = False
            if t["direction"] == "long":
                hit_tp = price >= t["tp"]
                hit_sl = price <= t["sl"]
            else:
                hit_tp = price <= t["tp"]
                hit_sl = price >= t["sl"]
            if hit_tp:
                c = self.close_trade(tid, price, "TP")
                if c: closed.append(c)
            elif hit_sl:
                c = self.close_trade(tid, price, "SL")
                if c: closed.append(c)
        return closed

    # ── stats ─────────────────────────────────────────────────

    def stats(self) -> dict:
        ct = self.closed_trades
        wins   = [t for t in ct if t["pnl"] > 0]
        losses = [t for t in ct if t["pnl"] <= 0]
        total_pnl = round(sum(t["pnl"] for t in ct), 4)
        winrate = round(len(wins) / len(ct) * 100, 1) if ct else 0.0
        avg_win  = round(sum(t["pnl"] for t in wins)   / len(wins),   4) if wins   else 0
        avg_loss = round(sum(t["pnl"] for t in losses) / len(losses), 4) if losses else 0
        return {
            "balance":        self.balance,
            "equity":         self.total_equity(),
            "available":      self.available_balance(),
            "total_pnl":      total_pnl,
            "pnl_pct":        round((self.balance - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100, 2),
            "total_trades":   len(ct),
            "open_trades":    len(self.open_trades),
            "wins":           len(wins),
            "losses":         len(losses),
            "winrate":        winrate,
            "avg_win":        avg_win,
            "avg_loss":       avg_loss,
        }
