from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional

def _ym(d: Optional[str]) -> str:
    if not d:
        return "unknown"
    return d[:7]

def build_trends(s) -> Dict[str, Any]:
    """
    Build trend data from extracted transactions in s.
    """
    
    txns = getattr(s, "extracted", []) or []
    cat_month = defaultdict(lambda: defaultdict(float))
    month_tot = defaultdict(float)
    
    for t in txns:
        amt = t.get("amount")
        
        try:
            a = float(amt)
        except Exception:
            continue
        
        ym = _ym(t.get("date"))
        vendor = t.get("vendor") or t.get("desc") or ""
        cat = None
        
        if hasattr(s, "budget_vendor_map"):
            cat = s.budget_vendor_map.get(vendor, None)
        if not cat:
            cat = "other"
            if hasattr(s, "budget_category_map"):
                cmap = s.budget_category_map
                sval = vendor.lower()
                
                for k, kws in cmap.items():
                    for kw in kws:
                        if kw and kw in sval:
                            cat = k
                            break
                    
                    if cat != "other":
                        break
        
        cat_month[cat][ym] += a
        month_tot[ym] += a

    months = sorted(month_tot.keys())
    totals = {c: sum(vals.values()) for c, vals in cat_month.items()}
    top = Counter(totals).most_common(6)
    categories = {}
    
    for c in cat_month:
        series = [ round(cat_month[c].get(m, 0.0), 2) for m in months ]
        categories[c] = series

    out = {
        "months": months,
        "categories": categories,
        "monthly_totals": {m: round(month_tot[m],2) for m in months},
        "top_categories": top
    }
    s.trend_data = out
    
    return out
