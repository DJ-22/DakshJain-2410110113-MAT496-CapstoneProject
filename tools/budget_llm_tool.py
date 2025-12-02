import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

BASE = Path(__file__).resolve().parents[1]
PROM_CAT = BASE / "prompts" / "budget_categorize_prompt.txt"
PROM_SUM = BASE / "prompts" / "budget_report_prompt.txt"
_CACHE = BASE / "data" / "vendor_category_cache.json"
_CACHE.parent.mkdir(parents=True, exist_ok=True)

def _load_prompt(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""

def _client() -> Optional[Any]:
    if OpenAI is None:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)

def _call_llm_system(system_prompt: str, user_content: str, model: str="gpt-4.1-mini") -> str:
    cli = _client()
    if cli is None:
        raise RuntimeError("OpenAI client unavailable or OPENAI_API_KEY not set")
    resp = cli.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_content}],
        temperature=0.0,
        max_tokens=800
    )
    # robust extraction
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        try:
            return resp.get("choices", [])[0].get("message", {}).get("content", "").strip()
        except Exception:
            return str(resp)

def _load_cache() -> Dict[str, str]:
    if not _CACHE.exists():
        return {}
    try:
        return json.loads(_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_cache(d: Dict[str, str]) -> None:
    try:
        _CACHE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def classify_vendors(vendors: List[str], model: str="gpt-4.1-mini") -> List[Dict[str,str]]:
    if not vendors:
        return []
    prompt = _load_prompt(PROM_CAT)
    user = json.dumps(vendors, ensure_ascii=False)
    txt = _call_llm_system(prompt, user, model=model)
    try:
        out = json.loads(txt)
        # validate shape
        res = []
        for o in out:
            if isinstance(o, dict) and "vendor" in o and "category" in o:
                res.append({"vendor": o["vendor"], "category": o["category"]})
        return res
    except Exception:
        return []

def summarize_budget(payload: Dict[str, Any], model: str="gpt-4.1-mini") -> Dict[str, Any]:
    prompt = _load_prompt(PROM_SUM)
    user = json.dumps(payload, ensure_ascii=False)
    txt = _call_llm_system(prompt, user, model=model)
    try:
        out = json.loads(txt)
        if isinstance(out, dict) and "answer" in out:
            return out
    except Exception:
        pass
    return {"answer": "", "recommendations": []}

def classify_vendors_with_cache(vendors: List[str], model: str="gpt-4.1-mini") -> Dict[str,str]:
    cache = _load_cache()
    to_query = [v for v in vendors if v not in cache]
    if to_query and _client() is not None:
        try:
            mapped = classify_vendors(to_query, model=model)
            for m in mapped:
                cache[m["vendor"]] = m["category"]
            _save_cache(cache)
        except Exception:
            pass
    # return mapping for all requested vendors (fallback to other)
    return {v: cache.get(v, "other") for v in vendors}
