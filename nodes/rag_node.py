import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from state.input_state import State
from .retrieval_node import run_retrieval

load_dotenv()
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "rag_prompt.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip() if PROMPT_PATH.exists() else (
    "You are an assistant answering questions about financial transactions. Use only the provided CONTEXT to answer."
)

def _build_context(retrieved: List[Dict[str, Any]], max_chars: int = 3000) -> str:
    """ 
    Builds context string from retrieved documents, limited to max_chars.
    """
    
    parts = []
    total = 0
    for r in retrieved:
        meta = r.get("meta") or {}
        doc = r.get("doc") or meta.get("desc") or ""
        block = (
            f"TXN_ID: {meta.get('txn_id','?')}\n"
            f"DATE: {meta.get('date')}\n"
            f"VENDOR: {meta.get('vendor')}\n"
            f"AMOUNT: {meta.get('amount')}\n"
            f"SOURCE: {meta.get('file')} (page {meta.get('page')})\n"
            f"DESC: {doc}\n"
        )
        
        if total + len(block) > max_chars:
            break
        
        parts.append(block)
        total += len(block)
    
    return "\n\n---\n\n".join(parts)

def _make_messages(query: str, context: str) -> List[Dict[str, str]]:
    """ 
    Constructs messages for OpenAI chat completion.
    """
    
    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{query}\n\n"
        "Return EXACTLY one JSON object as described in the system prompt."
    )
    
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

def _extract_text_from_response(resp) -> str:
    """
    Extracts text content from OpenAI response object.
    """
    
    try:
        return resp.choices[0].message.content.strip()
    except Exception:
        pass
    
    try:
        choices = resp.get("choices") if hasattr(resp, "get") else None
        if choices:
            first = choices[0]
            msg = first.get("message") or {}
            content = msg.get("content") or first.get("text")
            
            if content:
                return content.strip()
    except Exception:
        pass
    
    return str(resp)

def run_rag(
    s: State,
    query: str,
    top_k: int = 6,
    model: str = "gpt-4.1-mini",
    persist_dir: str = "data/vectorstore",
    collection_name: str = "transactions",
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """
    Runs a RAG (Retrieval-Augmented Generation) process:
    """

    retrieved = run_retrieval(
        s,
        query,
        top_k=top_k,
        persist_dir=persist_dir,
        collection_name=collection_name,
        model=None,
    )
    context = _build_context(retrieved)
    messages = _make_messages(query, context)

    if OpenAI is None:
        raise RuntimeError("openai package (v1+) not available. Install via `pip install openai`.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Set it to use run_rag().")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=600,
    )

    out_text = _extract_text_from_response(resp)
    cited_ids: List[str] = []
    parsed_json = None
    
    try:
        parsed = json.loads(out_text)
        if isinstance(parsed, dict) and "sources" in parsed and isinstance(parsed["sources"], list):
            parsed_json = parsed
            
            for cid in parsed["sources"]:
                if isinstance(cid, str):
                    cited_ids.append(cid)
    except Exception:
        parsed_json = None

    if not parsed_json:
        for line in out_text.splitlines():
            ln = line.strip()
            if ln.startswith("[") and "txn::" in ln:
                cited_ids.append(ln.strip("[]"))
            
            if ln.upper().startswith("TXN_ID:"):
                tok = ln.split(":", 1)[1].strip()
                if tok:
                    cited_ids.append(tok)

    seen = set()
    cited_ids = [x for x in cited_ids if x not in seen and not seen.add(x)]
    id2meta = { (r.get("meta") or {}).get("txn_id"): (r.get("meta") or {}) for r in retrieved }
    sources = [id2meta[x] for x in cited_ids if x in id2meta]
    fallback = [r.get("meta") or {} for r in retrieved[:min(3, len(retrieved))]]

    if parsed_json:
        answer_text = parsed_json.get("answer", "").strip()
    else:
        answer_text = out_text

    result = {
        "answer": answer_text,
        "sources": sources,
        "fallback_sources": fallback,
        "retrieved_count": len(retrieved),
        "cited_ids": cited_ids,
    }

    s.last_rag = {
        "query": query,
        "retrieved": len(retrieved),
        "sources_returned": len(sources),
        "cited_ids": cited_ids,
    }

    return result
