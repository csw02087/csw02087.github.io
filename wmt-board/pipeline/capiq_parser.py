"""
capiq_parser.py — Capital IQ "Financials" workbook (.xls) → raw_data JSON for the pipeline.

Sheets used: Key Stats, Income Statement, Balance Sheet, Cash Flow, Multiples,
Historical Capitalization, Capital Structure Summary, Ratios, Industry Specific, Segments.

Period labels are normalised to Walmart fiscal quarters: "Q2 Jul-31-2026" → "2Q27".
Every number carries a provenance tag (sheet, row label, column label) so the
validator can trace any figure in the note back to a cell.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List, Optional

import pandas as pd

MONTH_END_TO_Q = {"Apr": 1, "Jul": 2, "Oct": 3, "Jan": 4}


def period_key(label: str) -> Optional[str]:
    """'3 months\\nQ2\\nJul-31-2026' → '2Q27'; '12 months\\nJan-31-2026A' → 'FY26'; 'LTM…Jul-31-2026A' → 'LTM'."""
    s = str(label).replace("\n", " ")
    if "LTM" in s:
        return "LTM"
    m = re.search(r"(Jan|Apr|Jul|Oct)-\d{2}-(\d{4})", s)
    if not m:
        return None
    mon, yr = m.group(1), int(m.group(2))
    fy = yr + 1 if mon != "Jan" else yr           # FYE Jan: Jul-2026 → FY27
    if "12 months" in s:
        return f"FY{fy % 100:02d}" + ("E" if "E" in s.split(m.group(0))[-1][:3] else "")
    return f"{MONTH_END_TO_Q[mon]}Q{fy % 100:02d}"


class CapIQ:
    def __init__(self, path: str):
        self.x = pd.ExcelFile(path)
        self.path = path

    def _sheet(self, name: str) -> pd.DataFrame:
        df = self.x.parse(name, header=None).dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
        df.columns = range(df.shape[1])
        return df

    def _periods(self, df: pd.DataFrame, header_hint: str) -> tuple[int, Dict[int, str]]:
        for i in range(min(15, len(df))):
            if header_hint.lower() in str(df.iloc[i, 0]).lower():
                cols = {}
                for c in range(1, df.shape[1]):
                    k = period_key(df.iloc[i, c])
                    if k:
                        # CapIQ shows "Reclassified" duplicate columns; keep the LATEST column for a period
                        cols[c] = k
                return i, cols
        raise ValueError(f"period header '{header_hint}' not found")

    def table(self, sheet: str, header_hint: str, labels: Dict[str, str]) -> Dict[str, Dict[str, float]]:
        """Return {period: {field: value}} for the requested row labels (label → field name)."""
        df = self._sheet(sheet)
        hrow, cols = self._periods(df, header_hint)
        out: Dict[str, Dict[str, float]] = {}
        for i in range(hrow + 1, len(df)):
            lab = str(df.iloc[i, 0]).strip()
            if lab not in labels:
                continue
            field = labels[lab]
            for c, per in cols.items():
                v = df.iloc[i, c]
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                out.setdefault(per, {})[field] = v   # later (reclassified) columns overwrite earlier
        return out


IS_LABELS = {"Revenue": "ns", "Other Revenue": "mo", "Total Revenue": "rev", "Cost Of Goods Sold": "cogs", "Gross Profit": "gp",
             "Selling General & Admin Exp.": "sga", "Operating Income": "oi", "Net Interest Exp.": "int_net",
             "EBT Incl. Unusual Items": "pbt", "Income Tax Expense": "tax", "Net Income": "ni", "Minority Int. in Earnings": "nci",
             "Diluted EPS": "eps_gaap", "Diluted EPS Excl. Extra Items": "eps", "Normalized Diluted EPS": "eps_norm",
             "Weighted Avg. Diluted Shares Out.": "sh", "EBITDA": "ebitda", "EBIT": "ebit", "Dividends per Share": "dps",
             "Effective Tax Rate %": "taxrate", "Depreciation & Amort.": "da_is"}
BS_LABELS = {"Cash And Equivalents": "cash", "Total Receivables": "rec", "Inventory": "inv", "Prepaid Exp.": "pre", "Other Current Assets": "oca",
             "Total Current Assets": "tca", "Net Property, Plant & Equipment": "ppe", "Goodwill": "gw", "Other Long-Term Assets": "olta",
             "Total Assets": "ta", "Accounts Payable": "ap", "Accrued Exp.": "accr", "Short-term Borrowings": "stb", "Curr. Port. of LT Debt": "ltdc",
             "Curr. Port. of Leases": "leasec", "Curr. Income Taxes Payable": "acct", "Other Current Liabilities": "ocl", "Total Current Liabilities": "tcl",
             "Long-Term Debt": "ltd", "Long-Term Leases": "lease", "Def. Tax Liability, Non-Curr.": "dtl", "Other Non-Current Liabilities": "oncl",
             "Total Liabilities": "tl", "Retained Earnings": "re", "Comprehensive Inc. and Other": "aoci", "Total Common Equity": "twe",
             "Minority Interest": "nci", "Total Equity": "te", "Total Liabilities And Equity": "tle", "Total Debt": "total_debt", "Net Debt": "net_debt",
             "Total Shares Out. on Filing Date": "shares_out", "Book Value/Share": "bvps", "Full Time Employees": "employees"}
CF_LABELS = {"Net Income": "ni", "Depreciation & Amort., Total": "da", "(Gain) Loss On Sale Of Invest.": "inv", "Other Operating Activities": "oth",
             "Change in Acc. Receivable": "d_rec", "Change In Inventories": "d_inv", "Change in Acc. Payable": "d_ap", "Change in Inc. Taxes": "d_tax",
             "Change in Other Net Operating Assets": "d_oth", "Cash from Ops.": "cfo", "Capital Expenditure": "capex",
             "Sale of Property, Plant, and Equipment": "disp", "Cash Acquisitions": "acq", "Divestitures": "divest",
             "Invest. in Marketable & Equity Securt.": "strat", "Other Investing Activities": "othinv", "Cash from Investing": "cfi",
             "Total Debt Issued": "debt_iss", "Total Debt Repaid": "debt_rep", "Repurchase of Common Stock": "buyback",
             "Common Dividends Paid": "div", "Other Financing Activities": "othfin", "Cash from Financing": "cff",
             "Foreign Exchange Rate Adj.": "fx", "Net Change in Cash": "net", "Levered Free Cash Flow": "lfcf", "Unlevered Free Cash Flow": "ufcf"}
SEG_LABELS_REV = {"Walmart U.S.": "us", "Walmart International": "intl", "Sam's Club": "sams", "Corporate and Support": "corp", "Total Revenues": "total"}
IND_LABELS = {"Total Stores": "stores", "Total Same Store Sales Growth": "sss", "Online Revenues": "online_rev", "Retail Revenues": "retail_rev",
              "Total Retail Sq. Ft. (Net)": "sqft"}
MULT_LABELS = {"TEV/LTM EBITDA": "tev_ltm_ebitda", "TEV/NTM EBITDA": "tev_ntm_ebitda", "P/LTM EPS": "pe_ltm", "P/NTM EPS": "pe_ntm", "P/BV": "pbv"}
RATIO_LABELS = {"Return on Capital %": "roic", "Return on Equity %": "roe", "Inventory Turnover": "inv_turns", "Avg. Days Inventory Out.": "dio",
                "Avg. Cash Conversion Cycle": "ccc", "Net Debt/EBITDA": "nd_ebitda", "EBIT / Interest Exp.": "ebit_int_cover", "Altman Z Score": "altman"}


def segments(cq: CapIQ) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Segments sheet has repeated labels under section headers; walk sections explicitly."""
    df = cq._sheet("Segments")
    hrow, cols = cq._periods(df, "For the Fiscal Period Ending")
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    section = None
    sec_map = {"Revenues": "rev", "Gross Profit Before Tax": "gp", "Operating Profit Before Tax": "oi", "Capital Expenditure": "capex",
               "Depreciation & Amortization": "da", "Assets": "assets"}
    for i in range(hrow + 1, len(df)):
        lab = str(df.iloc[i, 0]).strip()
        if lab in sec_map:
            section = sec_map[lab]; continue
        if lab == "Geographic Segments":
            break
        if section and lab in SEG_LABELS_REV:
            f = SEG_LABELS_REV[lab]
            for c, per in cols.items():
                try:
                    v = float(df.iloc[i, c])
                except (TypeError, ValueError):
                    continue
                out.setdefault(per, {}).setdefault(section, {})[f] = v
    return out


def multiples(cq: CapIQ) -> List[Dict[str, Any]]:
    df = cq._sheet("Multiples")
    hrow = next(i for i in range(10) if "For Quarter Ending" in str(df.iloc[i, 0]))
    dates = [str(df.iloc[hrow, c])[:10] for c in range(1, df.shape[1])]
    rows = []
    for c in range(1, df.shape[1]):
        rec = {"as_of": dates[c - 1]}
        for i in range(hrow + 1, len(df)):
            lab = str(df.iloc[i, 0]).strip()
            if lab in MULT_LABELS:
                try:
                    rec[MULT_LABELS[lab]] = float(df.iloc[i, c])
                except (TypeError, ValueError):
                    pass
        if len(rec) > 1 and rec["as_of"] != "Average":
            rows.append(rec)
    return rows


def key_stats(cq: CapIQ) -> Dict[str, Any]:
    df = cq._sheet("Key Stats")
    hrow, cols = cq._periods(df, "For the Fiscal Period Ending")
    cons: Dict[str, Dict[str, float]] = {}
    labels = {"Total Revenue": "rev", "EBITDA": "ebitda", "EBIT": "ebit", "Net Income": "ni", "Diluted EPS Excl. Extra Items³": "eps", "Gross Profit": "gp"}
    for i in range(hrow + 1, hrow + 25):
        lab = str(df.iloc[i, 0]).strip()
        if lab in labels:
            for c, per in cols.items():
                try:
                    cons.setdefault(per, {})[labels[lab]] = float(df.iloc[i, c])
                except (TypeError, ValueError):
                    pass
    cap = {}
    for i in range(len(df)):
        lab = str(df.iloc[i, 0]).strip()
        for k, f in {"Share Price": "price", "Shares Out.": "shares_m", "Market Capitalization": "mcap", "- Cash & Short Term Investments": "cash",
                     "+ Total Debt": "total_debt", "= Total Enterprise Value (TEV)": "tev", "Book Value of Common Equity": "book_equity"}.items():
            if lab == k and f not in cap:
                try:
                    cap[f] = float(df.iloc[i, 1])
                except (TypeError, ValueError):
                    pass
    return {"consensus": cons, "capitalization": cap}


def build(path: str) -> Dict[str, Any]:
    cq = CapIQ(path)
    data = {
        "source": {"file": path.split("/")[-1], "provider": "S&P Capital IQ", "price_as_of": "2026-11-17"},
        "income": cq.table("Income Statement", "For the Fiscal Period Ending", IS_LABELS),
        "balance": cq.table("Balance Sheet", "Balance Sheet as of", BS_LABELS),
        "cashflow": cq.table("Cash Flow", "For the Fiscal Period Ending", CF_LABELS),
        "ratios": cq.table("Ratios", "For the Fiscal Period Ending", RATIO_LABELS),
        "industry": cq.table("Industry Specific", "For the Fiscal Period Ending", IND_LABELS),
        "segments": segments(cq),
        "multiples": multiples(cq),
        **key_stats(cq),
    }
    # derived annual FY from quarters where CapIQ gives only quarters
    for fy in ("FY23", "FY24", "FY25", "FY26"):
        qs = [f"{q}Q{fy[2:]}" for q in (1, 2, 3, 4)]
        if all(q in data["income"] for q in qs):
            agg = {}
            for k in ("ns", "mo", "rev", "cogs", "gp", "sga", "oi", "int_net", "pbt", "tax", "ni", "nci", "ebitda", "ebit", "da_is"):
                vals = [data["income"][q].get(k) for q in qs]
                if all(v is not None for v in vals):
                    agg[k] = sum(vals)
            agg["eps"] = round(sum(data["income"][q].get("eps", 0) for q in qs), 2)
            agg["sh"] = sum(data["income"][q].get("sh", 0) for q in qs) / 4
            data["income"].setdefault(fy, {}).update({k: v for k, v in agg.items() if k not in data["income"][fy]})
            cagg = {}
            for k in CF_LABELS.values():
                vals = [data["cashflow"].get(q, {}).get(k) for q in qs]
                if all(v is not None for v in vals):
                    cagg[k] = sum(vals)
            data["cashflow"].setdefault(fy, {}).update({k: v for k, v in cagg.items() if k not in data["cashflow"][fy]})
            data["balance"][fy] = data["balance"].get(f"4Q{fy[2:]}", {})
    return data


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "capiq_raw.json"
    d = build(src)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    print("periods IS:", sorted(d["income"].keys()))
    print("consensus:", d["consensus"])
    print("cap:", d["capitalization"])
    print("written", out)
