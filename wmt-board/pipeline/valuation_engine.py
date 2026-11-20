"""
valuation_engine.py — Deterministic valuation (professor's FCF-DCF framework, FY basis)
with quant risk support and multiple-based cross-checks.

Primary   : 5-year FCF DCF (EBIT·(1-t) + D&A − Capex − ΔNWC) + Gordon terminal value
WACC      : CAPM (rf + β·MRP) with β chosen from {Blume-adjusted regression, raw regression, CapIQ, peer-relevered};
            after-tax cost of debt; market-value weights (Market Value Balance Sheet)
Risk quant: WACC × g sensitivity grid; Monte Carlo (10,000 draws over β, MRP, g, revenue growth, EBITDA margin);
            bull / base / bear scenarios
Secondary : P/E (FY28E consensus EPS × own 5-yr NTM P/E band) and EV/EBITDA (own 5-yr NTM band) triangulation

Inputs : data/model_inputs.json, data/analysis.json, data/assumptions.json (human overrides, optional)
Output : data/valuation.json
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
YEARS = ["FY27E", "FY28E", "FY29E", "FY30E", "FY31E"]


def default_assumptions(an: Dict[str, Any]) -> Dict[str, Any]:
    R = an["recommendations"]
    return {
        "rev_growth": R["rev_growth"]["recommended"], "ebitda_margin": R["ebitda_margin"]["recommended"],
        "capex_pct": R["capex_pct"]["recommended"], "da_pct_capex": R["da_pct_capex"]["recommended"],
        "tax_rate": R["tax_rate"]["recommended"], "nca_pct": R["nca_pct"]["recommended"], "ncl_pct": R["ncl_pct"]["recommended"],
        "terminal_growth": R["terminal_growth"]["recommended"], "beta_choice": "blume", "beta_override": None,
        "risk_free": R["risk_free"]["recommended"], "mrp": R["mrp"]["recommended"], "cost_of_debt": R["cost_of_debt"]["recommended"],
        "pe_target_multiple": None, "ev_ebitda_target": None, "tolerance": 0.15, "market_return": 0.08, "buy_threshold": 0.05,
        "mc_draws": 10000, "mc_seed": 42,
        "source": "agent recommendations (H1 gate: edit data/assumptions.json to override)",
    }


def wacc_block(m: Dict[str, Any], an: Dict[str, Any], a: Dict[str, Any]) -> Dict[str, Any]:
    B = an["recommendations"]["beta"]
    choices = {"blume": B["blume_adjusted"], "regression": B["regression_5y_monthly"]["beta"], "capiq": B["capiq_5y"], "peer": B["relevered_from_peers"]}
    beta = a["beta_override"] if a.get("beta_override") else choices[a["beta_choice"]]
    ke = a["risk_free"] + beta * a["mrp"]
    mk = m["market"]
    E, Dv = mk["mcap"], mk["total_debt"]
    # professor's convention: weights on net debt vs enterprise value (EV = mcap + debt + nci + pref − cash)
    net_debt = Dv - mk["cash"]
    ev = E + Dv + mk["nci"] + mk["pref"] - mk["cash"]
    wd = net_debt / ev; we = 1 - wd
    t = a["tax_rate"][0]
    kd_after = a["cost_of_debt"] * (1 - t)
    wacc = we * ke + wd * kd_after
    return dict(beta=beta, beta_choices=choices, beta_se=B["regression_5y_monthly"]["se"], risk_free=a["risk_free"], mrp=a["mrp"], cost_of_equity=ke,
                cost_of_debt=a["cost_of_debt"], cost_of_debt_after_tax=kd_after, tax_rate=t, market_cap=E, total_debt=Dv, cash=mk["cash"],
                net_debt=net_debt, nci=mk["nci"], enterprise_value=ev, weight_debt=wd, weight_equity=we, wacc=wacc)


def project(m: Dict[str, Any], a: Dict[str, Any]) -> List[Dict[str, float]]:
    base = m["annual"]["FY26"]
    rows, rev, nwc_prev = [], base["rev"], base["nwc"]
    for i, y in enumerate(YEARS):
        rev = rev * (1 + a["rev_growth"][i])
        ebitda = rev * a["ebitda_margin"][i]
        capex = rev * a["capex_pct"][i]
        da = capex * a["da_pct_capex"][i]
        ebit = ebitda - da
        tax = a["tax_rate"][i]
        nopat = ebit * (1 - tax)
        nca, ncl = rev * a["nca_pct"][i], rev * a["ncl_pct"][i]
        nwc = nca - ncl
        d_nwc = nwc - nwc_prev; nwc_prev = nwc
        fcf = nopat + da - capex - d_nwc
        rows.append(dict(year=y, rev=rev, rev_growth=a["rev_growth"][i], ebitda=ebitda, ebitda_margin=a["ebitda_margin"][i], da=da, ebit=ebit,
                         ebit_margin=ebit / rev, tax_rate=tax, nopat=nopat, capex=capex, capex_pct=a["capex_pct"][i], nca=nca, ncl=ncl, nwc=nwc, d_nwc=d_nwc, fcf=fcf))
    return rows


def dcf(rows: List[Dict[str, float]], wacc: float, g: float, net_debt: float, nci: float, shares: float) -> Dict[str, float]:
    pv = sum(r["fcf"] / (1 + wacc) ** (i + 1) for i, r in enumerate(rows))
    tv = rows[-1]["fcf"] * (1 + g) / (wacc - g)
    pv_tv = tv / (1 + wacc) ** len(rows)
    ev = pv + pv_tv
    eq = ev - net_debt - nci
    return dict(pv_fcf=pv, terminal_value=tv, pv_terminal=pv_tv, enterprise_value=ev, equity_value=eq, per_share=eq / shares, tv_share=pv_tv / ev)


def run(m: Dict[str, Any], an: Dict[str, Any], a: Dict[str, Any]) -> Dict[str, Any]:
    W = wacc_block(m, an, a)
    rows = project(m, a)
    mk = m["market"]; shares = mk["shares_m"]; price = mk["price"]
    g = a["terminal_growth"]
    base = dcf(rows, W["wacc"], g, W["net_debt"], W["nci"], shares)

    # ---- sensitivity grid (WACC × g) -------------------------------------------------------------
    wacc_axis = [W["wacc"] + d for d in (-0.010, -0.005, 0.0, 0.005, 0.010)]
    g_axis = [g + d for d in (-0.010, -0.005, 0.0, 0.005, 0.010)]
    grid = [[dcf(rows, w, gg, W["net_debt"], W["nci"], shares)["per_share"] for gg in g_axis] for w in wacc_axis]

    # ---- scenarios ------------------------------------------------------------------------------
    def scen(dg, dm, dcapex, dbeta, dgt):
        a2 = dict(a); a2["rev_growth"] = [x + dg for x in a["rev_growth"]]; a2["ebitda_margin"] = [x + dm for x in a["ebitda_margin"]]
        a2["capex_pct"] = [x + dcapex for x in a["capex_pct"]]; a2["beta_override"] = W["beta"] + dbeta
        W2 = wacc_block(m, an, a2); r2 = project(m, a2)
        d2 = dcf(r2, W2["wacc"], g + dgt, W2["net_debt"], W2["nci"], shares)
        return dict(per_share=d2["per_share"], wacc=W2["wacc"], g=g + dgt, rev_growth=a2["rev_growth"][0], ebitda_margin=a2["ebitda_margin"][-1])
    scenarios = {"bull": scen(+0.010, +0.004, -0.003, -0.10, +0.005), "base": dict(per_share=base["per_share"], wacc=W["wacc"], g=g, rev_growth=a["rev_growth"][0], ebitda_margin=a["ebitda_margin"][-1]),
                 "bear": scen(-0.015, -0.005, +0.003, +0.15, -0.005)}

    # ---- Monte Carlo -----------------------------------------------------------------------------
    rng = np.random.default_rng(a["mc_seed"]); n = a["mc_draws"]
    betas = rng.normal(W["beta"], W["beta_se"], n)
    mrps = rng.normal(a["mrp"], 0.01, n)
    gs = np.clip(rng.normal(g, 0.005, n), 0.01, 0.045)
    growth_shift = rng.normal(0, 0.010, n)
    margin_shift = rng.normal(0, 0.003, n)
    kd = a["cost_of_debt"] * (1 - a["tax_rate"][0])
    res = np.empty(n)
    for i in range(n):
        ke = a["risk_free"] + betas[i] * mrps[i]
        w = W["weight_equity"] * ke + W["weight_debt"] * kd
        w = max(w, gs[i] + 0.01)
        rev, nwc_prev, fc = m["annual"]["FY26"]["rev"], m["annual"]["FY26"]["nwc"], []
        for k in range(5):
            rev *= 1 + a["rev_growth"][k] + growth_shift[i]
            ebitda = rev * (a["ebitda_margin"][k] + margin_shift[i]); capex = rev * a["capex_pct"][k]; da = capex * a["da_pct_capex"][k]
            nwc = rev * (a["nca_pct"][k] - a["ncl_pct"][k]); fc.append((ebitda - da) * (1 - a["tax_rate"][k]) + da - capex - (nwc - nwc_prev)); nwc_prev = nwc
        pv = sum(f / (1 + w) ** (k + 1) for k, f in enumerate(fc)); tv = fc[-1] * (1 + gs[i]) / (w - gs[i]) / (1 + w) ** 5
        res[i] = (pv + tv - W["net_debt"] - W["nci"]) / shares
    pct = np.percentile(res, [5, 10, 25, 50, 75, 90, 95])
    hist, edges = np.histogram(res, bins=40)
    mc = dict(draws=n, mean=float(res.mean()), median=float(pct[3]), std=float(res.std()), p5=float(pct[0]), p10=float(pct[1]), p25=float(pct[2]), p75=float(pct[4]), p90=float(pct[5]), p95=float(pct[6]),
              prob_above_price=float((res > price).mean()), prob_above_price_10pct=float((res > price * 1.10).mean()),
              hist=[int(h) for h in hist], edges=[float(e) for e in edges],
              inputs=dict(beta=(W["beta"], W["beta_se"]), mrp=(a["mrp"], 0.01), g=(g, 0.005), rev_growth_shift=(0, 0.01), margin_shift=(0, 0.003)))

    # ---- multiples cross-checks ------------------------------------------------------------------
    own = m["own_multiples"]; cons = m["consensus"]
    pe_mult = a["pe_target_multiple"] or own["pe_ntm_avg"]
    pe_band = [own["pe_ntm_p25"], own["pe_ntm_p75"]]
    pe_value = pe_mult * cons["FY28E"]["eps"]
    pe_value_band = [pe_band[0] * cons["FY28E"]["eps"], pe_band[1] * cons["FY28E"]["eps"]]
    ev_mult = a["ev_ebitda_target"] or own["ev_ntm_avg"]
    ev_value = (ev_mult * cons["FY28E"]["ebitda"] - W["net_debt"] - W["nci"]) / shares
    ev_value_band = [(own["ev_ntm_min"] * cons["FY28E"]["ebitda"] - W["net_debt"] - W["nci"]) / shares, (own["ev_ntm_max"] * cons["FY28E"]["ebitda"] - W["net_debt"] - W["nci"]) / shares]
    implied_pe = base["per_share"] / cons["FY28E"]["eps"]
    implied_ev = (base["enterprise_value"]) / cons["FY28E"]["ebitda"]
    current_pe = price / cons["FY28E"]["eps"]; current_ev = W["enterprise_value"] / cons["FY28E"]["ebitda"]

    # ---- reverse DCF: what the market price implies ---------------------------------------------
    target_eq = price * shares + W["net_debt"] + W["nci"]          # EV implied by market price
    def bisect(fn, lo, hi, it=60):
        for _ in range(it):
            mid = (lo + hi) / 2
            if fn(mid) > 0: hi = mid
            else: lo = mid
        return (lo + hi) / 2
    implied_g = bisect(lambda gg: dcf(rows, W["wacc"], gg, W["net_debt"], W["nci"], shares)["enterprise_value"] - target_eq, 0.0, W["wacc"] - 0.002)
    implied_wacc = bisect(lambda w: target_eq - dcf(rows, w, g, W["net_debt"], W["nci"], shares)["enterprise_value"], g + 0.002, 0.20)
    # 10-year FCF CAGR (from FY26 FCF) that reproduces the price at base WACC and g
    def ev_for_cagr(c):
        f0 = m["annual"]["FY26"]["fcf"]; fc = [f0 * (1 + c) ** (k + 1) for k in range(10)]
        return sum(f / (1 + W["wacc"]) ** (k + 1) for k, f in enumerate(fc)) + fc[-1] * (1 + g) / (W["wacc"] - g) / (1 + W["wacc"]) ** 10
    implied_fcf_cagr_10y = bisect(lambda c: ev_for_cagr(c) - target_eq, -0.2, 0.6)
    reverse = dict(market_ev=target_eq, implied_terminal_growth=implied_g, implied_wacc=implied_wacc, implied_fcf_cagr_10y=implied_fcf_cagr_10y,
                   fcf_yield_fy26=m["annual"]["FY26"]["fcf"] / mk["mcap"], fcf_yield_ltm=m["ltm"]["fcf"] / mk["mcap"])

    # ---- triangulation, flags, rating -----------------------------------------------------------
    tp = base["per_share"]
    flags = []
    if abs(pe_value / tp - 1) > a["tolerance"]:
        flags.append({"en": f"P/E cross-check (${pe_value:.0f} at {pe_mult:.1f}x FY28E) deviates {(pe_value/tp-1)*100:+.0f}% from DCF (${tp:.0f}): the market pays a multiple the cash-flow model does not reproduce.",
                      "ko": f"P/E 교차검증(${pe_value:.0f}, FY28E {pe_mult:.1f}x)이 DCF(${tp:.0f}) 대비 {(pe_value/tp-1)*100:+.0f}% 괴리: 시장이 지불하는 멀티플을 현금흐름 모델이 재현하지 못함."})
    if abs(ev_value / tp - 1) > a["tolerance"]:
        flags.append({"en": f"EV/EBITDA cross-check (${ev_value:.0f} at {ev_mult:.1f}x) deviates {(ev_value/tp-1)*100:+.0f}% from DCF.",
                      "ko": f"EV/EBITDA 교차검증(${ev_value:.0f}, {ev_mult:.1f}x)이 DCF 대비 {(ev_value/tp-1)*100:+.0f}% 괴리."})
    if base["tv_share"] > 0.80:
        flags.append({"en": f"Terminal value is {base['tv_share']*100:.0f}% of EV — valuation is dominated by the g/WACC spread.", "ko": f"터미널 가치가 EV의 {base['tv_share']*100:.0f}% — g/WACC 스프레드가 밸류에이션을 지배."})
    div_yield = 0.99 / price
    upside = tp / price - 1
    total = upside + div_yield
    excess = total - a["market_return"]
    rating = "BUY" if excess >= a["buy_threshold"] else "SELL" if excess <= -a["buy_threshold"] else "HOLD"

    return dict(assumptions=a, wacc=W, projection=rows, dcf=base, price=price, price_date=mk["price_date"], shares_m=shares, target_price=tp, upside=upside,
                dividend_yield=div_yield, total_return=total, market_return=a["market_return"], excess_return=excess, rating=rating,
                sensitivity=dict(wacc_axis=wacc_axis, g_axis=g_axis, grid=grid), scenarios=scenarios, monte_carlo=mc,
                multiples=dict(pe_multiple=pe_mult, pe_band=pe_band, pe_value=pe_value, pe_value_band=pe_value_band, ev_multiple=ev_mult, ev_value=ev_value, ev_value_band=ev_value_band,
                               implied_pe_fy28=implied_pe, implied_ev_ebitda_fy28=implied_ev, current_pe_fy28=current_pe, current_ev_ebitda_fy28=current_ev,
                               eps_fy28=cons["FY28E"]["eps"], ebitda_fy28=cons["FY28E"]["ebitda"], own_history=own),
                reverse_dcf=reverse, flags=flags)


if __name__ == "__main__":
    m = json.load(open(os.path.join(D, "model_inputs.json")))
    an = json.load(open(os.path.join(D, "analysis.json")))
    a = default_assumptions(an)
    p = os.path.join(D, "assumptions.json")
    if os.path.exists(p):
        a.update(json.load(open(p))); a["source"] = "human overrides (assumptions.json) on agent recommendations"
    else:
        json.dump(a, open(p, "w"), indent=1)
    v = run(m, an, a)
    json.dump(v, open(os.path.join(D, "valuation.json"), "w"), indent=1, default=float)
    W, dd = v["wacc"], v["dcf"]
    print(f"beta {W['beta']:.2f}  ke {W['cost_of_equity']*100:.2f}%  kd(at) {W['cost_of_debt_after_tax']*100:.2f}%  wD {W['weight_debt']*100:.1f}%  WACC {W['wacc']*100:.2f}%")
    for r in v["projection"]:
        print(f" {r['year']}: rev {r['rev']:,.0f} ({r['rev_growth']*100:.1f}%)  EBITDA {r['ebitda']:,.0f}  EBIT {r['ebit']:,.0f}  capex {r['capex']:,.0f}  dNWC {r['d_nwc']:,.0f}  FCF {r['fcf']:,.0f}")
    print(f"EV {dd['enterprise_value']:,.0f}  TV share {dd['tv_share']*100:.0f}%  equity {dd['equity_value']:,.0f}  per share ${dd['per_share']:.2f}  vs price ${v['price']}  upside {v['upside']*100:+.1f}%  rating {v['rating']}")
    print("scenarios:", {k: round(s['per_share'], 1) for k, s in v["scenarios"].items()})
    mc = v["monte_carlo"]; print(f"MC: median {mc['median']:.1f}  p5 {mc['p5']:.1f}  p95 {mc['p95']:.1f}  P(>price) {mc['prob_above_price']*100:.0f}%")
    M = v["multiples"]; print(f"P/E xcheck ${M['pe_value']:.0f} ({M['pe_multiple']:.1f}x; band {M['pe_value_band'][0]:.0f}-{M['pe_value_band'][1]:.0f}) | EV/EBITDA ${M['ev_value']:.0f} ({M['ev_multiple']:.1f}x) | implied P/E {M['implied_pe_fy28']:.1f}x cur {M['current_pe_fy28']:.1f}x")
    for f in v["flags"]:
        print(" FLAG:", f["en"])
