# WMT Assumption Board (FIN 5203)

Live page: `https://csw02087.github.io/wmt-board/`

A data-driven FCF-DCF "assumption board" for Walmart (WMT): every FCF driver shows its history, consensus,
peer median and the Historical-Analysis agent's recommendation; the human sets the final values and the page
recomputes WACC, DCF, sensitivity, scenarios, Monte Carlo and P/E · EV/EBITDA cross-checks live.

## Updating the numbers (two ways)

**A. Edit the JSON directly** — `data/board.json` holds every number the page uses (annual/quarterly series, consensus,
market data, betas, peers, recommendations, events). Change it, commit, push: the page re-reads it on load.
`data/assumptions.json` = the committed human assumptions (page default when the viewer has no local edits).

**B. Rebuild from Capital IQ** (local, since raw CapIQ data is licensed and git-ignored):
```
cd wmt-board/pipeline
pip install -r requirements.txt
# put files in input/:  capiq_wmt.xls  (Financials workbook)   prices/*.xls  (Charting exports: WMT, peers, ^SPX)
python build.py          # → ../data/board.json and ../index.html
git add ../data/board.json ../index.html && git commit -m "data: refresh" && git push
```
Pipeline: `capiq_parser.py → data_layer.py → historical_agent.py → valuation_engine.py → dashboard_build.py`.
Events behind flagged quarters live in `historical_agent.py` (`EVENTS`). Post-CapIQ quarters (e.g. 3Q27 from the 8-K)
are added in `data_layer.py` (`SUPP_3Q27`). Peer metrics: `comps_financials.json`.

## Files
- `index.html` — the board (self-contained; fetches `data/board.json` and `data/assumptions.json`)
- `data/board.json` — all numbers; `data/assumptions.json` — committed assumptions (H1 gate output)
- `pipeline/` — Python pipeline; `pipeline/input/` is git-ignored (CapIQ exports)
- `.github/workflows/wmt-board.yml` — regenerates `index.html` on pipeline changes (raw data stays local)
