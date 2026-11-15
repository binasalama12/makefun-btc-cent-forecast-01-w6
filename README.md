# btc-cent-forecast-01 — variant w6: volatility-scaled drift

Forecast Bitcoin's price 240 minutes after each checkpoint.

## Approach

Volatility-scaled drift over the 4,320 one-minute closes in each case:

- **Drift** = mean per-minute price change over the last 360 minutes.
- **Volatility ratio** = std of per-minute changes over the last 60 minutes
  divided by the same std over the last 1440 minutes, clamped to [0.3, 1.5].
  Recent volatility above the longer-term baseline amplifies the drift;
  calm recent minutes dampen it.
- **Forecast** = last close + 240 × drift × ratio, with the total move
  clamped to ±2% of the last close.
- **Fallback**: with fewer than 100 prices, forecast the last close
  (persistence).

Deterministic, standard library only, no network. Runs in well under the
8-second per-case cap.

## Run

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `*.in` in the input dir, writes `<id>.out` per case:
`{"forecasts": [{"case": "<id>", "price": <number>}]}`.

## License

MIT — see `LICENSE`.
