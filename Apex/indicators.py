def ema(values: list[float], period: int) -> list[float]:
    """Exponential Moving Average."""
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    result = [sum(values[:period]) / period]
    for v in values[period:]:
        result.append(v * k + result[-1] * (1 - k))
    return result

def rsi(closes: list[float], period: int = 14) -> list[float]:
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return []
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result = []
    for i in range(period, len(gains)):
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - 100 / (1 + rs))
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    return result

def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Returns (macd_line, signal_line, histogram) as lists.
    All three are aligned to the same length.
    """
    if len(closes) < slow + signal:
        return [], [], []
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    # align: ema_fast is longer than ema_slow
    offset = len(ema_fast) - len(ema_slow)
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]
    signal_line = ema(macd_line, signal)
    offset2 = len(macd_line) - len(signal_line)
    histogram = [macd_line[i + offset2] - signal_line[i] for i in range(len(signal_line))]
    # trim macd_line to match
    macd_trimmed = macd_line[offset2:]
    return macd_trimmed, signal_line, histogram

def bollinger(closes: list[float], period: int = 20, std_mult: float = 2.0):
    """Returns (upper, middle, lower) bands."""
    if len(closes) < period:
        return [], [], []
    upper, middle, lower = [], [], []
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1: i + 1]
        m = sum(window) / period
        std = (sum((x - m) ** 2 for x in window) / period) ** 0.5
        middle.append(m)
        upper.append(m + std_mult * std)
        lower.append(m - std_mult * std)
    return upper, middle, lower

def atr(highs, lows, closes, period: int = 14) -> list[float]:
    """Average True Range."""
    if len(closes) < period + 1:
        return []
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return []
    atr_vals = [sum(trs[:period]) / period]
    for tr in trs[period:]:
        atr_vals.append((atr_vals[-1] * (period - 1) + tr) / period)
    return atr_vals

def compute_all(candles: list[dict]) -> dict:
    """Compute all indicators from candle list."""
    if len(candles) < 50:
        return {}
    closes = [c["close"] for c in candles]
    highs  = [c["high"]  for c in candles]
    lows   = [c["low"]   for c in candles]
    ema9   = ema(closes, 9)
    ema21  = ema(closes, 21)
    rsi14  = rsi(closes, 14)
    macd_line, signal_line, histogram = macd(closes)
    return {
        "ema9":      ema9,
        "ema21":     ema21,
        "rsi":       rsi14,
        "macd":      macd_line,
        "macd_sig":  signal_line,
        "macd_hist": histogram,
        "closes":    closes,
    }
