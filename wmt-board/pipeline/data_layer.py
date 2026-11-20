"""
data_layer.py — Build model inputs (professor's 11-item FCF framework, FY basis)
from the CapIQ parse, comps file and daily prices. No LLM, no network.

Output: data/model_inputs.json
  annual  : FY23–FY26 actual (Key Stats annual lines + quarter aggregates), FY27E/FY28E consensus
  quarterly: 1Q23–2Q27 (18 quarters)
  items    : rev, ebitda, da, ebit, tax_rate, capex, cur_assets, cash, cur_liab, debt_in_cl,
             net_cur_assets, net_cur_liab, nwc, d_nwc, nopat, fcf  (+ margins / % of revenue)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")

QUARTERS = [f"{q}Q{y}" for y in (23, 24, 25, 26, 27) for q in (1, 2, 3, 4)][:19]
FYS = ["FY23", "FY24", "FY25", "FY26"]


def _g(dct: Dict, *keys, default=None):
    for k in keys:
        if k in dct and dct[k] is not None:
            return dct[k]
    return default


def build_period(raw: Dict[str, Any], p: str, prev_nwc: float | None) -> Dict[str, float]:
    inc, bs, cf = raw["income"].get(p, {}), raw["balance"].get(p, {}), raw["cashflow"].get(p, {})
    annual = raw["consensus"].get(p, {})            # Key Stats annual lines for FY periods
    rev = _g(annual, "rev") or _g(inc, "rev")
    ebitda = _g(annual, "ebitda") or _g(inc, "ebitda")
    ebit = _g(annual, "ebit") or _g(inc, "ebit")
    ni = _g(annual, "ni") or _g(inc, "ni")
    da = _g(cf, "da") or (ebitda - ebit if ebitda and ebit else None)
    pbt, tax = _g(inc, "pbt"), _g(inc, "tax")
    tax_rate = tax / pbt if pbt else 0.25
    capex = -_g(cf, "capex", default=0.0)
    cash = _g(bs, "cash", default=0.0)
    tca, tcl = _g(bs, "tca", default=0.0), _g(bs, "tcl", default=0.0)
    debt_in_cl = _g(bs, "stb", default=0.0) + _g(bs, "ltdc", default=0.0) + _g(bs, "leasec", default=0.0)
    nca, ncl = tca - cash, tcl - debt_in_cl
    nwc = nca - ncl
    d_nwc = (nwc - prev_nwc) if prev_nwc is not None else 0.0
    nopat = ebit * (1 - tax_rate)
    fcf = nopat + da - capex - d_nwc
    out = dict(rev=rev, gp=_g(annual, "gp") or _g(inc, "gp"), ebitda=ebitda, da=da, ebit=ebit, pbt=pbt, tax=tax, tax_rate=tax_rate,
               ni=ni, eps=_g(inc, "eps"), sh=_g(inc, "sh"), capex=capex, cur_assets=tca, cash=cash, cur_liab=tcl, debt_in_cl=debt_in_cl,
               net_cur_assets=nca, net_cur_liab=ncl, nwc=nwc, d_nwc=d_nwc, nopat=nopat, fcf=fcf,
               total_debt=_g(bs, "total_debt"), net_debt=_g(bs, "net_debt"), nci=_g(bs, "nci"), equity=_g(bs, "twe"),
               cfo=_g(cf, "cfo"), buyback=_g(cf, "buyback"), div=_g(cf, "div"), lfcf=_g(cf, "lfcf"),
               ebitda_margin=ebitda / rev, ebit_margin=ebit / rev, gm=(_g(annual, "gp") or _g(inc, "gp") or 0) / rev,
               da_pct_capex=da / capex if capex else None, capex_pct=capex / rev, nca_pct=nca / rev, ncl_pct=ncl / rev, ni_margin=ni / rev)
    return {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in out.items()}


# ---- 3Q FY27 supplement (Walmart 8-K, 19-Nov-2026; CapIQ workbook pre-dates the release) ----------
SUPP_3Q27 = {
    "income": dict(ns=186757, mo=2078, rev=188835, cogs=141003, gp=47832, sga=40062, oi=7770, ebit=7770, int_net=-685, pbt=6744, tax=1649,
                   ni=4945, eps=0.62, sh=7952, ebitda=7770 + (11763 - 7746), adj_eps=0.65, adj_oi=7770),
    "balance": dict(cash=13432, rec=12769, inv=70630, pre=4611, tca=101442, ppe=146694, gw=29027, olta=12274, ta=311615,
                    stb=12277, ap=71410, accr=32550, acct=487, ltdc=3221, leasec=1734 + 893, tcl=124556, ltd=41962, lease=15126 + 5939,
                    dtl=17271, twe=100223, nci=6245, te=106468, total_debt=12277 + 3221 + 41962 + 1734 + 893 + 15126 + 5939,
                    net_debt=12277 + 3221 + 41962 + 1734 + 893 + 15126 + 5939 - 13432, shares_out=7934.0),
    "cashflow_9m": dict(ni=17114, da=11763, inv=1296, cfo=29436, capex=-22621, buyback=-7830, div=-5913, debt_iss=10769, debt_rep=-3553, stb=5726),
    "kpi": dict(us_comp=2.9, us_transactions=1.5, us_ticket=1.4, us_ecom=23, global_ecom=17, global_ads=25, connect_ex_vizio=36, membership_fee=17,
                intl_sales_cc=3.3, sams_comp=4.9, gp_rate=24.5, gp_rate_chg_bp=28, opex_pct=21.5),
    "guidance_fy27": dict(sales_cc="+4.9–5.2%", adj_oi_cc="+8.0–8.6%", adj_eps="$2.84–2.89", capex_pct_sales=4.0, tax_rate="23.5–24.5%"),
    "source": "Walmart 8-K earnings release, 19-Nov-2026 (sec.gov 0000104169-26-000168)",
}


def _inject_supplement(raw: Dict[str, Any]) -> None:
    """Append 3Q27 to the CapIQ parse so the quarterly series runs 1Q23–3Q27 (19 quarters)."""
    raw["income"]["3Q27"] = SUPP_3Q27["income"]
    raw["balance"]["3Q27"] = SUPP_3Q27["balance"]
    six = {k: raw["cashflow"]["1Q27"].get(k, 0) + raw["cashflow"]["2Q27"].get(k, 0) for k in SUPP_3Q27["cashflow_9m"]}
    raw["cashflow"]["3Q27"] = {k: SUPP_3Q27["cashflow_9m"][k] - six[k] for k in six}
    raw["cashflow"]["3Q27"]["lfcf"] = None
    raw["segments"]["3Q27"] = {"rev": {"us": 124969, "intl": 35876, "sams": 25912, "total": 188835}, "oi": {"us": 6324, "intl": 1628, "sams": 547}}
    raw["industry"]["3Q27"] = {"stores": None, "sss": 0.029, "online_rev": None}


def build() -> Dict[str, Any]:
    raw = json.load(open(os.path.join(D, "capiq_raw.json")))
    _inject_supplement(raw)
    comps = json.load(open(os.path.join(D, "comps_financials.json")))
    px = pd.read_csv(os.path.join(D, "prices", "daily_close_5y.csv"), index_col=0, parse_dates=True)

    # ---- quarterly (NWC change computed quarter-over-quarter) --------------------
    quarterly, prev = {}, None
    for q in QUARTERS:
        if q not in raw["income"]:
            continue
        quarterly[q] = build_period(raw, q, prev)
        prev = quarterly[q]["nwc"]
    # ---- annual (NWC change year-over-year; FY22 NWC unavailable → 0 for FY23) -----
    annual, prev = {}, None
    for fy in FYS:
        annual[fy] = build_period(raw, fy, prev)
        prev = annual[fy]["nwc"]
    # growth
    for i, fy in enumerate(FYS[1:], 1):
        a, b = annual[fy], annual[FYS[i - 1]]
        a["rev_growth"] = a["rev"] / b["rev"] - 1
        a["ebitda_growth"] = a["ebitda"] / b["ebitda"] - 1
        a["fcf_growth"] = a["fcf"] / b["fcf"] - 1 if b["fcf"] else None
    qs = list(quarterly.keys())
    for i, q in enumerate(qs):
        if i >= 4:
            quarterly[q]["rev_yoy"] = quarterly[q]["rev"] / quarterly[qs[i - 4]]["rev"] - 1
            quarterly[q]["ebit_yoy"] = quarterly[q]["ebit"] / quarterly[qs[i - 4]]["ebit"] - 1
            quarterly[q]["ebitda_yoy"] = quarterly[q]["ebitda"] / quarterly[qs[i - 4]]["ebitda"] - 1

    # ---- LTM (to 2Q27) ----------------------------------------------------------------
    ltm_q = qs[-4:]
    ltm = {k: sum(quarterly[q][k] for q in ltm_q) for k in ("rev", "ebitda", "ebit", "da", "capex", "ni", "fcf", "nopat")}
    ltm["period"] = f"{ltm_q[0]}–{ltm_q[-1]}"

    # ---- market data ----------------------------------------------------------------
    cap = raw["capitalization"]
    last = quarterly[qs[-1]]
    price = float(px["WMT"].dropna().iloc[-1])
    shares = 7934.0
    market = dict(price=price, price_date=str(px["WMT"].dropna().index[-1].date()), shares_m=shares, mcap=price * shares,
                  cash=last["cash"], total_debt=last["total_debt"], nci=last["nci"], pref=0.0,
                  tev=price * shares + last["total_debt"] + last["nci"] - last["cash"],
                  book_equity=last["equity"], net_debt=last["total_debt"] - last["cash"], balance_date="2026-10-31 (3Q27)",
                  capiq_ref=dict(price=cap["price"], price_date="2026-11-17", tev=cap["tev"]),
                  last_close=price, last_close_date=str(px["WMT"].dropna().index[-1].date()),
                  high_52w=float(px["WMT"].iloc[-252:].max()), low_52w=float(px["WMT"].iloc[-252:].min()))
    cons = {k: raw["consensus"][k] for k in ("FY27E", "FY28E")}

    # ---- betas ------------------------------------------------------------------------
    def beta(tk, freq, years):
        p = px[[tk, "SPX"]].dropna()
        p = p[p.index >= p.index.max() - pd.DateOffset(years=years)]
        r = p.resample(freq).last().pct_change().dropna()
        x, y = r["SPX"].values, r[tk].values
        b = np.cov(x, y)[0, 1] / np.var(x, ddof=1)
        resid = y - (y.mean() - b * x.mean()) - b * x
        se = np.sqrt(resid.var(ddof=2) / ((x - x.mean()) ** 2).sum())
        r2 = np.corrcoef(x, y)[0, 1] ** 2
        return dict(beta=float(b), se=float(se), r2=float(r2), n=int(len(r)))
    betas = {}
    for tk in px.columns:
        if tk == "SPX":
            continue
        betas[tk] = {"m5y": beta(tk, "ME", 5), "w2y": beta(tk, "W-FRI", 2), "d1y": beta(tk, "D", 1)}
    # peer unlevered betas (Hamada) from comps file: D/Cap → D/E
    F = comps["fields"]
    peers = {}
    for tk, c in comps["companies"].items():
        v = dict(zip(F, c["v"]))
        if tk in ("CA", "OKEY"):
            continue
        dc = (v["debt_cap"] or 0) / 100
        de = dc / (1 - dc) if dc < 1 else None
        b_capiq = v["beta_5y"]
        b_reg = betas.get(tk, {}).get("m5y", {}).get("beta")
        peers[tk] = dict(name=c["name"], group=c["group"], de=de, beta_capiq=b_capiq, beta_reg=b_reg,
                         unlev_capiq=(b_capiq / (1 + (1 - 0.25) * de)) if (b_capiq and de is not None) else None,
                         unlev_reg=(b_reg / (1 + (1 - 0.25) * de)) if (b_reg and de is not None) else None,
                         **{k: v[k] for k in F})

    # ---- own multiples history (CapIQ Multiples sheet) ---------------------------------
    mult = raw["multiples"]
    pe_ntm = [m["pe_ntm"] for m in mult if m.get("pe_ntm")]
    ev_ntm = [m["tev_ntm_ebitda"] for m in mult if m.get("tev_ntm_ebitda")]
    own_mult = dict(pe_ntm_avg=float(np.mean(pe_ntm)), pe_ntm_min=float(np.min(pe_ntm)), pe_ntm_max=float(np.max(pe_ntm)),
                    pe_ntm_p25=float(np.percentile(pe_ntm, 25)), pe_ntm_p75=float(np.percentile(pe_ntm, 75)),
                    ev_ntm_avg=float(np.mean(ev_ntm)), ev_ntm_min=float(np.min(ev_ntm)), ev_ntm_max=float(np.max(ev_ntm)),
                    series=mult)

    # ---- segments & industry (quarterly) -------------------------------------------------
    seg = {q: raw["segments"].get(q) for q in qs if raw["segments"].get(q)}
    ind = {q: raw["industry"].get(q) for q in qs if raw["industry"].get(q)}

    out = dict(meta=dict(company="Walmart Inc.", ticker="WMT", fye="January", basis="Fiscal year (FY27 = Feb-2026..Jan-2027)",
                         source="S&P Capital IQ (Financials workbook, Comps, Charting exports) as of 2026-11-17/19"),
               annual=annual, quarterly=quarterly, ltm=ltm, market=market, consensus=cons, betas=betas, peers=peers,
               own_multiples=own_mult, segments=seg, industry=ind, ratios={q: raw["ratios"].get(q) for q in qs},
               supplement_3q27=SUPP_3Q27)
    with open(os.path.join(D, "model_inputs.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=float)
    return out


if __name__ == "__main__":
    m = build()
    print("annual:")
    for fy, a in m["annual"].items():
        print(f" {fy}: rev {a['rev']:,.0f}  EBITDA {a['ebitda']:,.0f} ({a['ebitda_margin']*100:.1f}%)  EBIT {a['ebit']:,.0f}  tax {a['tax_rate']*100:.1f}%  capex {a['capex']:,.0f} ({a['capex_pct']*100:.1f}%)  NWC {a['nwc']:,.0f}  dNWC {a['d_nwc']:,.0f}  FCF {a['fcf']:,.0f}")
    print("LTM:", {k: round(v) for k, v in m['ltm'].items() if k != 'period'})
    print("market:", m["market"])
    print("WMT beta:", m["betas"]["WMT"])
    print("own multiples:", {k: round(v, 1) for k, v in m["own_multiples"].items() if k != "series"})
    print("peers unlevered (capiq):", {k: round(v["unlev_capiq"], 2) for k, v in m["peers"].items() if v["unlev_capiq"]})
