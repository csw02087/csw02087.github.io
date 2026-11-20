"""
historical_agent.py — Historical Analysis Agent (deterministic statistics + event library).

Runs BEFORE any growth assumption is applied. For each driver of the FCF model it computes
CAGR, linear trend, seasonality, flags abnormal quarters (|z| of y/y change > 1.5), attaches the
researched event behind each flag, and proposes a recommended assumption with its rationale,
alongside consensus and peer medians — the "board" a human sets assumptions from (H1 gate).

Output: data/analysis.json
"""
from __future__ import annotations

import json
import os
from statistics import mean, median, pstdev
from typing import Any, Dict, List

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")

# ---------------------------------------------------------------------------------------------- #
# Event library — researched from 8-K releases, 10-K, sell-side notes (dates = fiscal quarter)
# ---------------------------------------------------------------------------------------------- #
EVENTS: Dict[str, List[Dict[str, str]]] = {
    "1Q23": [{"tag": "inventory", "en": "Inventory +33% y/y to $61.2bn; markdowns and fuel/wage cost surge; profit warning (May-2022)", "ko": "재고 +33% y/y($612억), 마크다운·연료·인건비 급등, 이익 경고(2022.5)"}],
    "2Q23": [{"tag": "inventory", "en": "Inventory glut persists ($59.9bn, +25%); general-merchandise markdowns compress gross margin", "ko": "재고 과잉 지속($599억, +25%), 일반상품 마크다운으로 매출총이익률 압박"}],
    "4Q23": [{"tag": "one-off", "en": "Opioid settlement charge ($3.3bn) and Flipkart/PhonePe reorganisation hit EBIT and lift effective tax rate (FY23 33.6%)", "ko": "오피오이드 합의금($33억)·Flipkart/PhonePe 재편 비용으로 EBIT 감소, FY23 유효세율 33.6%로 상승"}],
    "1Q24": [{"tag": "demand", "en": "Revenue +7.6% y/y: grocery share gains from higher-income households, food inflation still ~mid-single digit, e-commerce +26%", "ko": "매출 +7.6% y/y: 고소득층 식료품 점유율 확대, 식품 인플레이션 중단일자릿수, 이커머스 +26%"}],
    "1Q25": [{"tag": "margin", "en": "EBIT margin 4.2%: advertising +24% and membership income lift mix; inventory -2.7% y/y", "ko": "EBIT 마진 4.2%: 광고 +24%·멤버십 수익으로 믹스 개선; 재고 -2.7% y/y"}],
    "2Q25": [{"tag": "margin", "en": "EBIT margin 4.7% (record 2Q): Walmart Connect +30%, gross margin +43bp, e-commerce losses narrowing; raised FY25 guide", "ko": "EBIT 마진 4.7%(2Q 최고): Walmart Connect +30%, GM +43bp, 이커머스 손실 축소; FY25 가이던스 상향"}],
    "3Q25": [{"tag": "margin", "en": "EBIT margin 4.0%: 3rd straight guidance raise; advertising +28%; VIZIO deal pending", "ko": "EBIT 마진 4.0%: 3회 연속 가이던스 상향; 광고 +28%; VIZIO 인수 대기"}],
    "1Q26": [{"tag": "demand", "en": "Revenue +2.5% y/y (slowest since FY21): lapping leap day and calendar shift, tariff uncertainty, FX headwind on International; EPS miss first in years", "ko": "매출 +2.5% y/y(FY21 이후 최저): 윤일·캘린더 효과 역기저, 관세 불확실성, 해외 FX 역풍; 수년 만의 EPS 미스"}],
    "4Q24": [{"tag": "corporate", "en": "3-for-1 stock split (Feb-2024); VIZIO acquisition announced ($2.3bn); FY24 e-commerce $100bn+", "ko": "3:1 액면분할(2024.2), VIZIO 인수 발표($23억), FY24 이커머스 $1,000억 돌파"}],
    "4Q25": [{"tag": "corporate", "en": "VIZIO acquisition closed (Dec-2024); advertising revenue FY25 $4.4bn (+27%)", "ko": "VIZIO 인수 완료(2024.12), FY25 광고 매출 $44억(+27%)"}],
    "2Q26": [{"tag": "one-off", "en": "$400m legal settlement (CapIQ reclassifies to unusual items: EBIT 7,686 vs reported 7,286); tariff cost absorption begins", "ko": "법적 합의금 $4억(CapIQ는 비경상 항목으로 재분류: EBIT 7,686 vs 공시 7,286), 관세 비용 흡수 시작"}],
    "3Q26": [{"tag": "non-operating", "en": "$2.1bn gain on equity investments below EBIT; CEO succession announced (Furner from Feb-2026); 7th straight quarter of e-commerce >20%", "ko": "지분투자 평가이익 $21억(영업외), CEO 교체 발표(2026.2 Furner), 7분기 연속 이커머스 >20%"}],
    "4Q26": [{"tag": "seasonal", "en": "Holiday quarter: revenue $190.7bn, EBIT $8.7bn; FY26 advertising $6.4bn; capex 3.7% of sales", "ko": "연말 성수기: 매출 $1,907억, EBIT $87억; FY26 광고 $64억; Capex 매출의 3.7%"}],
    "1Q27": [{"tag": "corporate", "en": "First quarter under CEO John Furner; membership & other income +27% to $2.1bn", "ko": "John Furner CEO 첫 분기; 멤버십·기타수익 +27%($21억)"}],
    "2Q27": [{"tag": "one-off", "en": "~$2.9bn tariff refund booked in cost of sales (CapIQ reclassifies to unusual: EBIT 6,483 vs reported 9,383); $1.2bn investment loss; U.S. comp +2.6% miss (H&W -125bp); capex guide raised to 4.0%; stock -9%", "ko": "관세환급 ~$29억 매출원가 반영(CapIQ는 비경상 재분류: EBIT 6,483 vs 공시 9,383); 투자손실 $12억; 미국 동일점포 +2.6% 미스(H&W -125bp); Capex 가이던스 4.0%로 상향; 주가 -9%"}],
    "3Q27": [{"tag": "capex", "en": "Symbotic $6bn automation expansion (25 DCs, 30-Oct); $3bn 4-tranche bond (20-Oct); Flipkart BBD timing shifts Intl growth; FY27 guide raised (adj. EPS $2.84-2.89); inventory $70.6bn (+8%)", "ko": "Symbotic $60억 자동화 확대(25개 DC, 10/30); $30억 4트랜치 채권(10/20); Flipkart BBD 시점 이동으로 해외 성장 왜곡; FY27 가이던스 상향(조정 EPS $2.84-2.89); 재고 $706억(+8%)"}],
}

SEASON_LABEL = {1: "1Q (Feb-Apr)", 2: "2Q (May-Jul)", 3: "3Q (Aug-Oct)", 4: "4Q (Nov-Jan, holiday)"}


def cagr(first: float, last: float, years: float) -> float:
    return (last / first) ** (1 / years) - 1 if first > 0 and last > 0 else float("nan")


def linear_trend(xs: List[float]) -> Dict[str, float]:
    x = np.arange(len(xs)); y = np.array(xs, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum() if y.var() > 0 else 0
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2), "next": float(slope * len(xs) + intercept)}


def analyse(m: Dict[str, Any]) -> Dict[str, Any]:
    A, Q = m["annual"], m["quarterly"]
    fys = list(A.keys()); qs = list(Q.keys())
    out: Dict[str, Any] = {"drivers": {}, "anomalies": [], "seasonality": {}, "recommendations": {}, "notes": []}

    # ---- driver statistics (annual) ------------------------------------------------------------
    for key, label in [("rev", "Revenue"), ("ebitda", "EBITDA"), ("ebit", "EBIT"), ("da", "D&A"), ("capex", "Capex"), ("fcf", "Free cash flow"), ("ni", "Net income")]:
        series = [A[f][key] for f in fys]
        out["drivers"][key] = {"label": label, "annual": dict(zip(fys, series)),
                               "cagr_3y": cagr(series[0], series[-1], len(series) - 1),
                               "yoy": {fys[i]: series[i] / series[i - 1] - 1 for i in range(1, len(series))},
                               "trend": linear_trend(series)}
    for key, label in [("ebitda_margin", "EBITDA margin"), ("ebit_margin", "EBIT margin"), ("gm", "Gross margin"), ("tax_rate", "Effective tax rate"),
                       ("capex_pct", "Capex % revenue"), ("da_pct_capex", "D&A % capex"), ("nca_pct", "Net current assets % rev"), ("ncl_pct", "Net current liabilities % rev")]:
        series = [A[f][key] for f in fys]
        out["drivers"][key] = {"label": label, "annual": dict(zip(fys, series)), "mean": mean(series), "last": series[-1],
                               "trend": linear_trend(series), "stdev": pstdev(series)}

    # ---- seasonality (share of FY revenue / EBIT by quarter, FY23–FY26) ------------------------
    for key in ("rev", "ebit", "capex"):
        shares = {q: [] for q in (1, 2, 3, 4)}
        for fy in fys:
            tot = sum(Q[f"{q}Q{fy[2:]}"][key] for q in (1, 2, 3, 4))
            for q in (1, 2, 3, 4):
                shares[q].append(Q[f"{q}Q{fy[2:]}"][key] / tot)
        out["seasonality"][key] = {SEASON_LABEL[q]: mean(v) for q, v in shares.items()}

    # ---- anomaly detection on quarterly y/y growth (z-score) ------------------------------------
    for key, label in [("rev", "Revenue y/y"), ("ebit", "EBIT y/y"), ("ebitda", "EBITDA y/y")]:
        g = {q: Q[q].get(f"{key}_yoy") for q in qs if Q[q].get(f"{key}_yoy") is not None}
        vals = list(g.values()); mu, sd = mean(vals), pstdev(vals)
        for q, v in g.items():
            z = (v - mu) / sd if sd else 0
            if abs(z) > 1.5:
                out["anomalies"].append({"quarter": q, "metric": label, "value": v, "z": z, "mean": mu,
                                         "events": EVENTS.get(q, [{"tag": "n/a", "en": "No catalogued event — investigate", "ko": "등록된 이벤트 없음 — 조사 필요"}])})
    # margin level anomalies (quarterly EBIT margin vs same quarter prior years)
    for q in qs[4:]:
        qn = int(q[0]); hist = [Q[p]["ebit_margin"] for p in qs if int(p[0]) == qn and p != q and p < q]
        if len(hist) >= 3:
            mu, sd = mean(hist), pstdev(hist)
            z = (Q[q]["ebit_margin"] - mu) / sd if sd else 0
            if abs(z) > 2.0:
                out["anomalies"].append({"quarter": q, "metric": "EBIT margin vs same-quarter history", "value": Q[q]["ebit_margin"], "z": z, "mean": mu,
                                         "events": EVENTS.get(q, [{"tag": "n/a", "en": "No catalogued event", "ko": "등록된 이벤트 없음"}])})
    out["anomalies"].sort(key=lambda a: a["quarter"])
    out["events"] = EVENTS

    # ---- recommendations (what the human sees on the board) --------------------------------------
    cons = m["consensus"]; peers = m["peers"]
    core = [k for k, v in peers.items() if v["group"] == "core"]
    pm = lambda f: median([peers[k][f] for k in core if peers[k].get(f) is not None])  # noqa: E731
    rev_c = out["drivers"]["rev"]["cagr_3y"]
    cons_g27 = cons["FY27E"]["rev"] / A["FY26"]["rev"] - 1
    cons_g28 = cons["FY28E"]["rev"] / cons["FY27E"]["rev"] - 1
    R = out["recommendations"]
    R["rev_growth"] = {"label": "Revenue growth (FY27E→FY31E)", "history_cagr_3y": rev_c, "ltm_yoy": m["ltm"]["rev"] / sum(Q[q]["rev"] for q in qs[-8:-4]) - 1,
                       "consensus": {"FY27E": cons_g27, "FY28E": cons_g28}, "guidance_fy27": "+4.9–5.2% cc (19-Nov-26)", "peer_median_ltm": pm("rev_g_ltm") / 100,
                       "recommended": [0.050, 0.043, 0.040, 0.038, 0.035],
                       "rationale_en": "Fade from the FY27 guide (+4.9–5.2% cc) toward the 3-yr CAGR floor (~5.3%) less inflation normalisation; e-commerce (+17–23%) and advertising (+25%) keep growth above the core-peer median (5.5%) while store growth is <1%/yr.",
                       "rationale_ko": "FY27 가이던스(+4.9~5.2% cc)에서 출발해 3년 CAGR(~5.3%)에서 인플레이션 정상화분을 뺀 수준으로 점진 둔화. 이커머스(+17~23%)·광고(+25%)가 핵심 피어 중앙값(5.5%)보다 높은 성장을 유지하되 점포 증가는 연 1% 미만."}
    em = out["drivers"]["ebitda_margin"]
    R["ebitda_margin"] = {"label": "EBITDA margin", "history_mean": em["mean"], "last": em["last"], "ltm": m["ltm"]["ebitda"] / m["ltm"]["rev"],
                          "consensus": {"FY27E": cons["FY27E"]["ebitda"] / cons["FY27E"]["rev"], "FY28E": cons["FY28E"]["ebitda"] / cons["FY28E"]["rev"]},
                          "peer_median_ltm": pm("ebitda_m_ltm") / 100, "recommended": [0.0645, 0.0660, 0.0675, 0.0685, 0.0695],
                          "rationale_en": "Mix shift (advertising, membership, marketplace) adds ~10–15bp/yr; consensus already embeds 6.5% (FY27E) → 6.8% (FY28E). Recommendation sits at/just below consensus to allow for price reinvestment (rollbacks) and wage inflation.",
                          "rationale_ko": "광고·멤버십·마켓플레이스 믹스 전환으로 연 10~15bp 개선; 컨센서스는 이미 6.5%(FY27E)→6.8%(FY28E) 반영. 롤백 가격 재투자·임금 인플레이션을 감안해 컨센서스와 같거나 약간 낮게 추천."}
    cp = out["drivers"]["capex_pct"]
    R["capex_pct"] = {"label": "Capex % revenue", "history_mean": cp["mean"], "last": cp["last"], "ltm": m["ltm"]["capex"] / m["ltm"]["rev"], "guidance_fy27": 0.040,
                      "recommended": [0.040, 0.040, 0.038, 0.036, 0.035],
                      "rationale_en": "Guidance 4.0% for FY27 (Symbotic 25-DC automation, remodels, delivery density); step down toward the 3.5% long-run level once the automation programme is built out (FY29E+).",
                      "rationale_ko": "FY27 가이던스 4.0%(Symbotic 25개 DC 자동화, 리모델, 배송 밀도); 자동화 프로그램 완성 후(FY29E~) 장기 평균 3.5%로 하향."}
    dp = out["drivers"]["da_pct_capex"]
    R["da_pct_capex"] = {"label": "D&A % capex", "history_mean": dp["mean"], "last": dp["last"], "recommended": [0.55, 0.57, 0.60, 0.63, 0.66],
                         "rationale_en": "D&A lags capex; ratio fell from 65% (FY23) to 53% (FY26) during the investment cycle and should recover as capex intensity normalises.",
                         "rationale_ko": "D&A는 Capex에 후행; 투자 사이클 중 65%(FY23)→53%(FY26)로 하락했고 Capex 강도 정상화와 함께 회복 예상."}
    tr = out["drivers"]["tax_rate"]
    R["tax_rate"] = {"label": "Effective tax rate", "history_mean": tr["mean"], "last": tr["last"], "guidance_fy27": "23.5–24.5%", "recommended": [0.240] * 5,
                     "rationale_en": "FY23 (33.6%) distorted by opioid settlement non-deductibility; FY24–FY26 23–26%; guidance 23.5–24.5%.",
                     "rationale_ko": "FY23(33.6%)는 오피오이드 합의금 비공제로 왜곡; FY24~26 23~26%; 가이던스 23.5~24.5%."}
    R["nca_pct"] = {"label": "Net current assets % revenue", "history_mean": out["drivers"]["nca_pct"]["mean"], "last": out["drivers"]["nca_pct"]["last"], "recommended": [out["drivers"]["nca_pct"]["mean"]] * 5,
                    "rationale_en": "Stable at ~10% of revenue; inventory growth (3Q27 +8%) running ahead of sales is the watch item.",
                    "rationale_ko": "매출의 ~10%로 안정적; 재고 증가(3Q27 +8%)가 매출보다 빠른 점이 관찰 포인트."}
    R["ncl_pct"] = {"label": "Net current liabilities % revenue", "history_mean": out["drivers"]["ncl_pct"]["mean"], "last": out["drivers"]["ncl_pct"]["last"], "recommended": [out["drivers"]["ncl_pct"]["mean"]] * 5,
                    "rationale_en": "Supplier-financed model: payables + accruals ~13% of revenue; held at the 4-yr mean.",
                    "rationale_ko": "공급업체 금융 모델: 매입채무+미지급 ~13%; 4년 평균 유지."}
    R["terminal_growth"] = {"label": "Terminal growth", "recommended": 0.030, "range": [0.025, 0.035],
                            "rationale_en": "Nominal GDP-type growth; below the 3-yr revenue CAGR (5.3%) and consensus FY28E (+4.3%).",
                            "rationale_ko": "명목 GDP 수준; 3년 매출 CAGR(5.3%)·컨센 FY28E(+4.3%)보다 낮게."}
    b = m["betas"]["WMT"]
    peer_unlev = [v["unlev_capiq"] for v in peers.values() if v["group"] == "core" and v["unlev_capiq"]]
    R["beta"] = {"label": "Equity beta", "regression_5y_monthly": b["m5y"], "regression_2y_weekly": b["w2y"], "capiq_5y": peers["WMT"]["beta_capiq"],
                 "blume_adjusted": 1 / 3 + 2 / 3 * b["m5y"]["beta"], "peer_unlevered_median": median(peer_unlev),
                 "relevered_from_peers": median(peer_unlev) * (1 + 0.75 * (m["market"]["total_debt"] / m["market"]["mcap"])),
                 "recommended": round(1 / 3 + 2 / 3 * b["m5y"]["beta"], 2),
                 "rationale_en": f"Regression beta 0.51 (R² {b['m5y']['r2']:.2f}, SE {b['m5y']['se']:.2f}) ≈ CapIQ 0.53; Blume adjustment (⅓·1 + ⅔·β) gives 0.67, which we adopt because low-R² betas mean-revert and CFA-style practice uses it. Peer-relevered beta (~0.5) is the lower bound.",
                 "rationale_ko": f"회귀 베타 0.51(R² {b['m5y']['r2']:.2f}, 표준오차 {b['m5y']['se']:.2f}) ≈ CapIQ 0.53; Blume 조정(⅓·1+⅔·β) 0.67을 채택 — 낮은 R²의 베타는 평균회귀하며 CFA 실무 관행. 피어 리레버 베타(~0.5)는 하한."}
    R["cost_of_debt"] = {"label": "Pre-tax cost of debt", "recommended": 0.045,
                         "rationale_en": "Weighted coupon of outstanding notes ~4.0%; new 2026 issues priced 4.9–5.75% (WMT29B 4.875%, WMT30B 5.75%); AA rating.",
                         "rationale_ko": "기발행 채권 가중 쿠폰 ~4.0%; 2026년 신규 발행 4.9~5.75%(WMT29B 4.875%, WMT30B 5.75%); AA 등급."}
    R["risk_free"] = {"label": "Risk-free rate", "recommended": 0.0395, "rationale_en": "1-month T-bill 3.95% (class convention); 10-yr Treasury ~4.1% as sensitivity.", "rationale_ko": "1개월 T-bill 3.95%(수업 기준); 10년물 ~4.1%는 민감도."}
    R["mrp"] = {"label": "Market risk premium", "recommended": 0.055, "rationale_en": "5.5% (class assumption; Damodaran implied ERP 4.3–5.5%).", "rationale_ko": "5.5%(수업 가정; Damodaran 내재 ERP 4.3~5.5%)."}

    out["notes"] = [
        {"en": "EBIT basis: CapIQ reclassifies the 2Q27 tariff refund (~$2.9bn) and the 2Q26 legal settlement ($0.4bn) to unusual items, so CapIQ EBIT differs from reported operating income in those quarters. Annual FY lines use CapIQ Key Stats; 3Q27 uses the 8-K as reported.",
         "ko": "EBIT 기준: CapIQ는 2Q27 관세환급(~$29억)과 2Q26 법적합의금($4억)을 비경상 항목으로 재분류하므로 해당 분기 EBIT가 공시 영업이익과 다름. 연간 FY는 CapIQ Key Stats, 3Q27은 8-K 공시 기준."},
        {"en": "Prices are split-adjusted but not dividend-adjusted (CapIQ 'Share Pricing'); betas are therefore price-return betas.", "ko": "주가는 분할 조정, 배당 미조정(CapIQ 'Share Pricing'); 베타는 가격수익률 기준."},
    ]
    return out


if __name__ == "__main__":
    m = json.load(open(os.path.join(D, "model_inputs.json")))
    a = analyse(m)
    with open(os.path.join(D, "analysis.json"), "w") as fh:
        json.dump(a, fh, indent=1, default=float)
    print("CAGR 3y:", {k: round(v["cagr_3y"] * 100, 1) for k, v in a["drivers"].items() if "cagr_3y" in v})
    print("seasonality rev:", {k: round(v * 100, 1) for k, v in a["seasonality"]["rev"].items()})
    print("anomalies:")
    for x in a["anomalies"]:
        print(f"  {x['quarter']} {x['metric']:38s} {x['value']*100:6.1f}%  z={x['z']:+.1f}  -> {x['events'][0]['en'][:80]}")
    print("recommended beta:", a["recommendations"]["beta"]["recommended"], "| rev growth:", a["recommendations"]["rev_growth"]["recommended"])
