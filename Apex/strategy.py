from bot2.indicators import compute_all

TP_PCT = 0.001   # 0.1%
SL_PCT = 0.001   # 0.1%

def get_signal(candles: list[dict]) -> str | None:
    """
    Returns 'long', 'short', or None.
    Entry conditions:
      LONG:  EMA9 > EMA21  AND  RSI < 60  AND  MACD histogram > 0
      SHORT: EMA9 < EMA21  AND  RSI > 40  AND  MACD histogram < 0
    """
    ind = compute_all(candles)
    if not ind:
        return None

    ema9  = ind["ema9"]
    ema21 = ind["ema21"]
    rsi   = ind["rsi"]
    hist  = ind["macd_hist"]

    # Need at least 2 values to detect crossover
    if len(ema9) < 2 or len(ema21) < 2 or len(rsi) < 1 or len(hist) < 1:
        return None

    # Align by taking last values
    e9_now  = ema9[-1];   e9_prev  = ema9[-2]
    e21_now = ema21[-1];  e21_prev = ema21[-2]
    rsi_now = rsi[-1]
    h_now   = hist[-1];   h_prev   = hist[-2] if len(hist) >= 2 else 0

    # Crossover detection (stronger signal)
    crossed_up   = e9_prev <= e21_prev and e9_now > e21_now
    crossed_down = e9_prev >= e21_prev and e9_now < e21_now

    # Trend confirmation (no crossover needed, just alignment)
    trend_up   = e9_now > e21_now
    trend_down = e9_now < e21_now

    # MACD momentum
    macd_bull = h_now > 0
    macd_bear = h_now < 0

    # RSI filters
    rsi_ok_long  = 40 < rsi_now < 65
    rsi_ok_short = 35 < rsi_now < 60

    # LONG: crossover OR strong alignment + MACD bull + RSI ok
    if (crossed_up or trend_up) and macd_bull and rsi_ok_long:
        return "long"

    # SHORT: crossover OR strong alignment + MACD bear + RSI ok
    if (crossed_down or trend_down) and macd_bear and rsi_ok_short:
        return "short"

    return None

def calculate_tp_sl(entry_price: float, direction: str) -> tuple[float, float]:
    """Returns (take_profit_price, stop_loss_price)."""
    if direction == "long":
        tp = entry_price * (1 + TP_PCT)
        sl = entry_price * (1 - SL_PCT)
    else:
        tp = entry_price * (1 - TP_PCT)
        sl = entry_price * (1 + SL_PCT)
    return round(tp, 6), round(sl, 6)
