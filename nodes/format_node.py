from typing import Dict, Any, List

def format_rag_result(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats the RAG node result to include only relevant fields.
    """
    
    out = {
        "answer": r.get("answer", ""),
        "sources": []
    }
    
    for s in r.get("sources", []):
        out["sources"].append({
            "txn_id": s.get("txn_id"),
            "date": s.get("date"),
            "vendor": s.get("vendor"),
            "amount": s.get("amount"),
            "currency": s.get("currency"),
            "file": s.get("file"),
            "page": s.get("page"),
            "desc": s.get("desc")
        })
    
    return out
