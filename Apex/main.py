import time
import threading
from datetime import datetime

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

from bot2.feed      import get_ohlcv, get_all_prices
from bot2.strategy  import get_signal, calculate_tp_sl
from bot2.portfolio import Portfolio

# ── app setup ────────────────────────────────────────────────
app       = Flask(__name__, template_folder="../templates2")
socketio  = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
portfolio = Portfolio()

SYMBOLS   = ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "ADA/USD"]
INTERVAL  = 5    # candle interval in minutes
COOLDOWN  = 120  # seconds between trades per symbol
BOT_ACTIVE = True

# ── bot loop ─────────────────────────────────────────────────
def bot_loop():
    """Main trading loop: runs every 60 seconds."""
    while True:
        try:
            prices = get_all_prices()
            if not prices:
                time.sleep(10)
                continue

            # 1. Check exits
            closed = portfolio.check_exits(prices)
            for t in closed:
                socketio.emit("trade_closed", t)

            # 2. Look for new entries
            if BOT_ACTIVE:
                for symbol in SYMBOLS:
                    if not portfolio.can_open(symbol, COOLDOWN):
                        continue
                    candles = get_ohlcv(symbol, interval=INTERVAL, limit=120)
                    if len(candles) < 50:
                        continue
                    signal = get_signal(candles)
                    if not signal:
                        continue
                    price = prices.get(symbol)
                    if not price:
                        continue
                    tp, sl = calculate_tp_sl(price, signal)
                    trade  = portfolio.open_trade(symbol, signal, price, tp, sl)
                    socketio.emit("trade_opened", trade)

            # 3. Broadcast state
            _broadcast_state(prices)

        except Exception as e:
            print(f"[bot_loop error] {e}")

        time.sleep(60)

def _broadcast_state(prices: dict):
    """Push current state to all connected clients."""
    open_list = []
    for t in portfolio.open_trades.values():
        p = prices.get(t["symbol"], t["entry_price"])
        portfolio.update_unrealized(t["id"], p)
        open_list.append({**t})

    socketio.emit("state_update", {
        "stats":        portfolio.stats(),
        "open_trades":  open_list,
        "prices":       prices,
        "timestamp":    datetime.utcnow().strftime("%H:%M:%S UTC"),
    })

# ── routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def api_state():
    prices = get_all_prices()
    for t in portfolio.open_trades.values():
        p = prices.get(t["symbol"], t["entry_price"])
        portfolio.update_unrealized(t["id"], p)
    return jsonify({
        "stats":         portfolio.stats(),
        "open_trades":   list(portfolio.open_trades.values()),
        "closed_trades": portfolio.closed_trades[-50:],
        "prices":        prices,
    })

@app.route("/api/candles/<path:symbol>")
def api_candles(symbol):
    symbol = symbol.replace("-", "/")
    candles = get_ohlcv(symbol, interval=INTERVAL, limit=100)
    return jsonify(candles)

# ── socketio events ───────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    prices = get_all_prices()
    for t in portfolio.open_trades.values():
        p = prices.get(t["symbol"], t["entry_price"])
        portfolio.update_unrealized(t["id"], p)
    socketio.emit("state_update", {
        "stats":        portfolio.stats(),
        "open_trades":  list(portfolio.open_trades.values()),
        "prices":       prices,
        "timestamp":    datetime.utcnow().strftime("%H:%M:%S UTC"),
    })

# ── start ─────────────────────────────────────────────────────
if __name__ == "__main__":
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
