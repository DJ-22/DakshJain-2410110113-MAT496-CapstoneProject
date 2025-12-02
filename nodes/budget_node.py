from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

try:
    from tools.budget_llm_tool import classify_vendors_with_cache, summarize_budget
except Exception:
    classify_vendors_with_cache = None
    summarize_budget = None

def _default_map():
    return {
        "food": ["starbucks", "pizza", "burger", "taco", "restaurant", "dine", "eat", "ubereats", "doordash"],
        "groceries": ["grocer", "freshgrocer", "trader", "whole foods", "fresh", "superstore"],
        "rent": ["landlord", "rent"],
        "transport": ["uber", "lyft", "taxi", "metro", "bus", "train", "deltaair", "uber eats"],
        "entertainment": ["cinema", "movie", "ticketmaster", "steam", "regal", "concert", "netflix", "spotify"],
        "utilities": ["power", "electric", "city power", "verizon", "aws", "phone", "internet"],
        "shopping": ["amazon", "target", "apple", "macbook", "store", "mart"],
        "health": ["pharmacy", "cvs", "clinic", "hospital"],
        "gym": ["gym", "iron pump", "membership"],
        "travel": ["delta", "airlines", "flight", "hotel"],
        "other": []
    }

def _cat_from_vendor_kw(vendor: Optional[str], cmap: Dict[str, List[str]]) -> str:
    if not vendor:
        return "other"
    s = vendor.lower()
    for cat, kws in cmap.items():
        for kw in kws:
            if kw and kw in s:
                return cat
    return "other"

def _ym_from_date(d: Optional[str]) -> str:
    if not d:
        return "unknown"
    try:
        return d[:7]
    except Exception:
        return "unknown"

def run_budget(s, budget_cfg: Optional[Dict[str, float]] = None, cmap: Optional[Dict[str, List[str]]] = None, use_llm: bool = True) -> Any:
    txns = getattr(s, "extracted", []) or []
    if cmap is None:
        cmap = _default_map()
    if budget_cfg is None:
        budget_cfg = {}

    # first pass: keyword mapping and collect unmapped vendors
    vendor_map = {}
    unmapped = set()
    for t in txns:
        vendor = (t.get("vendor") or t.get("desc") or "").strip()
        cat = _cat_from_vendor_kw(vendor, cmap)
        vendor_map[vendor] = cat
        if cat == "other" and vendor:
            unmapped.add(vendor)

    # try LLM classification for unmapped vendors (cached)
    if use_llm and classify_vendors_with_cache is not None and unmapped:
        try:
            mapping = classify_vendors_with_cache(list(unmapped))
            for v, c in mapping.items():
                vendor_map[v] = c or vendor_map.get(v, "other")
        except Exception:
            pass

    # aggregation
    cat_tot = defaultdict(float)
    month_tot = defaultdict(float)
    month_cat = defaultdict(lambda: defaultdict(float))
    cnt = 0
    for t in txns:
        amt = t.get("amount")
        if amt is None:
            continue
        try:
            a = float(amt)
        except Exception:
            continue
        vendor = (t.get("vendor") or t.get("desc") or "").strip()
        cat = vendor_map.get(vendor, "other")
        ym = _ym_from_date(t.get("date"))
        cat_tot[cat] += a
        month_tot[ym] += a
        month_cat[ym][cat] += a
        cnt += 1

    top_c = Counter(cat_tot).most_common(5)

    violations = []
    for ym, cats in month_cat.items():
        for cat, val in cats.items():
            limit = budget_cfg.get(cat)
            if limit is None:
                continue
            if val > limit:
                violations.append({
                    "month": ym,
                    "category": cat,
                    "spent": round(val,2),
                    "limit": round(limit,2),
                    "excess": round(val - limit, 2)
                })

    res = {
        "count_indexed_txns": cnt,
        "total_by_category": {k: round(v,2) for k,v in cat_tot.items()},
        "total_by_month": {k: round(v,2) for k,v in month_tot.items()},
        "month_category_breakdown": {m: {c: round(v,2) for c,v in cats.items()} for m,cats in month_cat.items()},
        "top_categories": [{"category": k, "amount": round(v,2)} for k,v in top_c],
        "violations": violations
    }

    # optional LLM summary
    summary = None
    recs = []
    if use_llm and summarize_budget is not None:
        try:
            payload = {
                "total_by_category": res["total_by_category"],
                "month_category_breakdown": res["month_category_breakdown"],
                "violations": res["violations"]
            }
            summary = summarize_budget(payload)
            recs = summary.get("recommendations", []) if isinstance(summary, dict) else []
            summary_text = summary.get("answer", "") if isinstance(summary, dict) else ""
        except Exception:
            summary_text = ""
            recs = []
    else:
        summary_text = ""

    s.budget_results = res
    s.budget_config_used = budget_cfg
    s.budget_category_map = cmap
    s.budget_vendor_map = vendor_map
    s.budget_report = summary_text
    s.budget_recommendations = recs
    return s
