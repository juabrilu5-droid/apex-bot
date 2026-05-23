"""
APEX Bot — main.py
Flask + SocketIO + bot loop
Timezone: UTC-3 (Buenos Aires) en todos los logs y eventos emitidos al dashboard
"""

import time
import threading
from datetime import datetime, timezone, timedelta

from flask import Flask, send_file
from flask_socketio import SocketIO

from feed import get_ohlcv as get_candles
from strategy import get_signal
from portfolio import open_trade, check_and_close, get_summary, INITIAL_CAPITAL

# ── App ──
app = Flask(__name__)
app.config["SECRET_KEY"] = "apex-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Timezone Buenos Aires (UTC-3) ──
TZ_BA = timezone(timedelta(hours=-3))

SYMBOLS    = ["BTC/USD", "ETH/USD", "SOL/USD"]
INTERVAL   = 5      # velas de 5 minutos (entero, no string)
LOOP_SLEEP = 60     # segundos entre iteraciones del bot


def ba_now() -> datetime:
    """Retorna datetime actual en hora Buenos Aires."""
    return datetime.now(TZ_BA)


def ba_now_str() -> str:
    return ba_now().strftime("%H:%M:%S")


def log(msg: str) -> None:
    print(f"[{ba_now_str()} ART] {msg}", flush=True)


def bot_loop() -> None:
    log("Bot iniciado — pares activos: BTC, ETH, SOL")
    while True:
        try:
            for symbol in SYMBOLS:
                candles = get_candles(symbol, INTERVAL)
                if not candles or len(candles) < 30:
                    continue

                current_price = candles[-1]["close"]

                # Verificar si hay que cerrar posición abierta
                closed = check_and_close(symbol, current_price)
                if closed:
                    log(f"CERRADO {symbol} {closed['dir']} | "
                        f"Entrada: {closed['entry']:.2f} | "
                        f"Salida: {closed['exit']:.2f} | "
                        f"PnL: {closed['pnl']:+.2f} | "
                        f"Razón: {closed['reason']}")
                    socketio.emit("trade_closed", {
                        "symbol":     symbol,
                        "dir":        closed["dir"],
                        "entry":      closed["entry"],
                        "exit":       closed["exit"],
                        "pnl":        round(closed["pnl"], 2),
                        "reason":     closed["reason"],
                        "opened_at":  closed["opened_at"].strftime("%H:%M:%S"),
                        "closed_at":  closed["closed_at"].strftime("%H:%M:%S"),
                        "time":       closed["closed_at"].strftime("%H:%M:%S"),
                    })

                # Intentar abrir nueva posición
                signal = get_signal(symbol, candles)
                if signal:
                    trade = open_trade(symbol, signal, current_price)
                    if trade:
                        log(f"ABIERTO {symbol} {signal} @ {current_price:.2f} | "
                            f"TP: {trade['tp']:.2f} | SL: {trade['sl']:.2f}")
                        socketio.emit("trade_opened", {
                            "symbol":    symbol,
                            "dir":       signal,
                            "entry":     current_price,
                            "tp":        round(trade["tp"], 4),
                            "sl":        round(trade["sl"], 4),
                            "opened_at": ba_now_str(),
                        })

            # Emitir resumen actualizado al dashboard
            summary = get_summary()
            summary["timestamp"] = ba_now_str()
            summary["timestamp_full"] = ba_now().strftime("%d/%m/%Y %H:%M:%S ART")
            socketio.emit("summary_update", summary)

        except Exception as exc:
            log(f"ERROR en bot_loop: {exc}")

        time.sleep(LOOP_SLEEP)


# ── Rutas Flask ──
@app.route("/")
def index():
    return send_file("index.html")


@app.route("/health")
def health():
    return {"status": "ok", "time_art": ba_now_str()}, 200


# ── SocketIO eventos ──
@socketio.on("connect")
def on_connect():
    summary = get_summary()
    summary["timestamp"]      = ba_now_str()
    summary["timestamp_full"] = ba_now().strftime("%d/%m/%Y %H:%M:%S ART")
    socketio.emit("summary_update", summary)


# ── Arranque ──
if __name__ == "__main__":
    thread = threading.Thread(target=bot_loop, daemon=True)
    thread.start()
    socketio.run(app, host="0.0.0.0", port=7860, debug=False)
