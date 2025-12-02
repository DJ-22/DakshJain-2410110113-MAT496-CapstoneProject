import os
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
from .trend_node import build_trends

def _ensure_dir(p: Path):
    """ 
    Ensure directory exists. 
    """
    
    p.mkdir(parents=True, exist_ok=True)

def save_line_chart(x: List[str], ys: List[List[float]], labels: List[str], out_path: Path, title: str = ""):
    """
    Save a line chart to the specified path.
    """
    
    plt.figure(figsize=(10,5))
    for y, lab in zip(ys, labels):
        plt.plot(x, y, label=lab)
    
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close()

def save_bar_chart(x: List[str], heights: List[float], out_path: Path, title: str = ""):
    """ 
    Save a bar chart to the specified path.
    """
    
    plt.figure(figsize=(10,5))
    plt.bar(x, heights)
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(str(out_path))
    plt.close()

def make_charts(s, out_dir: str = "data/charts", top_n: int = 5) -> Dict[str, str]:
    """ 
    Generate and save charts based on trend data in s.
    """

    p = Path(out_dir)
    _ensure_dir(p)

    td = getattr(s, "trend_data", None)
    if td is None:
        td = build_trends(s)

    months = td.get("months", [])
    monthly_totals = [td["monthly_totals"].get(m, 0.0) for m in months]
    top = td.get("top_categories", [])[:top_n]
    cats = [c for c, _ in top]
    ys = [td["categories"].get(c, [0]*len(months)) for c in cats]
    out = {}

    if cats:
        fname = p / f"top_{top_n}_categories_trend.png"
        save_line_chart(months, ys, cats, fname, title=f"Top {top_n} categories - Monthly trend")
        out["top_categories_trend"] = str(fname)

    if months:
        fname2 = p / "monthly_totals.png"
        save_bar_chart(months, monthly_totals, fname2, title="Total spending per month")
        out["monthly_totals"] = str(fname2)

    s.chart_paths = out
    
    return out
