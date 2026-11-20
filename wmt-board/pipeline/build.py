"""
build.py — one-shot rebuild of the board from inputs.

Inputs (pipeline/input/, NOT committed — licensed data):
  capiq_wmt.xls                 Capital IQ Financials workbook (WMT)
  prices/*.xls                  Capital IQ Charting exports (WMT, peers, ^SPX) → merged to prices/daily_close_5y.csv
  comps_financials.json         peer metrics (committed, derived)
Outputs: ../data/board.json (+ index.html refreshed), data/*.json intermediates in pipeline/data/
"""
import glob, os, re, subprocess, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); INP = os.path.join(HERE, "input"); DATA = os.path.join(HERE, "data"); SITE = os.path.dirname(HERE)
os.makedirs(os.path.join(DATA, "prices"), exist_ok=True)
xls = os.path.join(INP, "capiq_wmt.xls")
if not os.path.exists(xls):
    sys.exit("missing pipeline/input/capiq_wmt.xls")
# merge price exports
frames = {}
for f in glob.glob(os.path.join(INP, "prices", "*.xls")):
    df = pd.read_excel(f, sheet_name=0, header=None).dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    name = str(df.iloc[0, 1]); m = re.search(r"\(([^)]+)\)", name); tk = "SPX" if "SPX" in name else (m.group(1).split(":")[-1] if m else name)
    d = df.iloc[1:].copy(); d.columns = ["date"] + list(df.iloc[0, 1:]); d["date"] = pd.to_datetime(d["date"]); frames[tk] = d.set_index("date").iloc[:, -1].astype(float)
if frames:
    pd.DataFrame(frames).sort_index().to_csv(os.path.join(DATA, "prices", "daily_close_5y.csv"))
import shutil; shutil.copy(xls, os.path.join(DATA, "capiq_wmt.xls")); shutil.copy(os.path.join(HERE, "comps_financials.json"), os.path.join(DATA, "comps_financials.json"))
env = dict(os.environ, BOARD_OUT=SITE)
for step in (["capiq_parser.py", os.path.join(DATA, "capiq_wmt.xls"), os.path.join(DATA, "capiq_raw.json")], ["data_layer.py"], ["historical_agent.py"], ["valuation_engine.py"], ["dashboard_build.py"]):
    print(">>", step[0]); subprocess.run([sys.executable] + step, cwd=HERE, env=env, check=True)
print("done →", os.path.join(SITE, "data", "board.json"))
