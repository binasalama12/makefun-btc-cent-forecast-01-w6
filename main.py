#!/usr/bin/env python3
"""btc-cent-forecast-01 — variant w6: volatility-scaled drift (Python 3.13, stdlib only).

Approach: take the mean per-minute drift over the last 360 minutes and scale
it by recent volatility relative to longer-term volatility:

    drift   = mean of per-minute price changes over the last 360 minutes
    vol60   = std of per-minute changes over the last 60 minutes
    vol1440 = std of per-minute changes over the last 1440 minutes
    ratio   = clamp(vol60 / vol1440, 0.3, 1.5)
    forecast = last_close + 240 * drift * ratio

The total move is clamped to +/-2% of the last close, so a noisy short window
cannot throw the guess far. With fewer than 100 prices the fallback is the
last close (persistence). Deterministic: no randomness, no network.
"""

import json
import math
import os

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9999999.99999

DRIFT_WINDOW = 360      # minutes used for the mean drift
VOL_SHORT = 60          # minutes for recent volatility
VOL_LONG = 1440         # minutes for baseline volatility
HORIZON = 240           # minutes ahead to forecast
SCALE_MIN = 0.3
SCALE_MAX = 1.5
MOVE_CLAMP = 0.02       # max |move| as a fraction of last close
MIN_PRICES = 100


def price5(x):
    """Clamp x to the scorer's (0, 10_000_000) range, rounded to 5 decimals."""
    x = min(MAX_PRICE, max(MIN_PRICE, x))
    return round(x, 5)


def _mean(xs):
    return sum(xs) / len(xs)


def _std(xs):
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def forecast(prices):
    """Volatility-scaled drift forecast for one price series."""
    if len(prices) < MIN_PRICES:
        return price5(prices[-1])

    last = prices[-1]
    if not isinstance(last, (int, float)) or not math.isfinite(last):
        raise ValueError("last price is not a finite number")
    deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    if not all(math.isfinite(d) for d in deltas):
        raise ValueError("price series contains a non-finite value")

    # Mean per-minute drift over the last 360 minutes.
    drift_deltas = deltas[-DRIFT_WINDOW:]
    drift = _mean(drift_deltas)

    # Volatility: std of per-minute changes, recent vs. long window.
    short = deltas[-VOL_SHORT:]
    long_ = deltas[-VOL_LONG:]
    vol_short = _std(short)
    vol_long = _std(long_)
    if vol_long > 0:
        ratio = vol_short / vol_long
    else:
        ratio = 1.0
    ratio = min(SCALE_MAX, max(SCALE_MIN, ratio))

    move = HORIZON * drift * ratio
    # Clamp the total move to +/-2% of the last close.
    cap = MOVE_CLAMP * abs(last)
    move = min(cap, max(-cap, move))
    return price5(last + move)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for fname in inputs:
        case_id = fname[: -len(".in")]
        with open(os.path.join(INPUT_DIR, fname), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{fname} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or not prices:
            raise ValueError(f"{fname} market has no prices")
        last = prices[-1]
        if not isinstance(last, (int, float)) or not math.isfinite(last):
            raise ValueError(f"{fname} last price is not finite")
        out = {"forecasts": [{"case": case_id, "price": forecast(prices)}]}
        with open(os.path.join(OUTPUT_DIR, case_id + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
