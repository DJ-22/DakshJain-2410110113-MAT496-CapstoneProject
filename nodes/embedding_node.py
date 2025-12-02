import os
import math
from typing import List
from pathlib import Path
from state.input_state import State
from tools.validator import validate
from .vector_db_node import VectorStore

try:
    import openai
except Exception:
    openai = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

def _make_id(fn: str, page, idx: int) -> str:
    """ 
    Make a unique ID for a transaction embedding 
    """
    
    p = Path(fn).name
    pg = "p{}".format(page) if page is not None else "pn"
    
    return f"txn::{p}::{pg}::{idx}"

def _text_for_embed(t: dict) -> str:
    """ 
    Create a text representation for embedding from transaction dict
    """
    
    parts = []
    for k in ("vendor", "desc", "amount", "date", "source"):
        v = t.get(k)
        if v:
            parts.append(str(v))
   
    return " | ".join(parts) if parts else t.get("desc", "")

def _openai_embeds(texts: List[str], model: str = "text-embedding-3-small"):
    """ 
    Get embeddings for a list of texts using OpenAI API.
    """
    
    if openai is None:
        raise RuntimeError("openai package not available or not configured")
    
    res = openai.Embedding.create(model=model, input=texts)
    return [r["embedding"] for r in res["data"]]

def _sbert_embeds(texts: List[str], model: str = "all-MiniLM-L6-v2"):
    """ 
    Get embeddings for a list of texts using SentenceTransformer.
    """
    
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed")
    
    m = SentenceTransformer(model)
    return m.encode(texts, show_progress_bar=False).tolist()

def run_embeddings(s: State, persist_dir: str = "data/vectorstore", collection_name: str = "transactions",
                   model: str = None, batch_size: int = 64) -> State:
    """ 
    Run the embedding process on extracted transactions and store them in the vector store.
    """
    
    arr = getattr(s, "extracted", []) or []
    if not arr:
        s.embedded_count = 0
        return s

    vs = VectorStore(persist_dir=persist_dir, collection_name=collection_name)

    use_openai = False
    if model and model.startswith("text-") and openai is not None and os.getenv("OPENAI_API_KEY"):
        use_openai = True

    texts = []
    ids = []
    metas = []
    docs = []

    for i, t in enumerate(arr):
        if not validate(t):
            continue
        
        tid = _make_id(t.get("file", "nofile"), t.get("page"), i)
        txt = _text_for_embed(t)
        meta = {
            "txn_id": tid,
            "date": t.get("date"),
            "vendor": t.get("vendor"),
            "amount": t.get("amount"),
            "currency": t.get("currency"),
            "file": t.get("file"),
            "page": t.get("page"),
            "source": t.get("source"),
            "desc": t.get("desc")
        }
        ids.append(tid)
        texts.append(txt)
        metas.append(meta)
        docs.append(txt)

    total = len(texts)
    emb_count = 0
    
    for st in range(0, total, batch_size):
        ed = min(total, st + batch_size)
        batch_txt = texts[st:ed]
        
        if use_openai:
            emb = _openai_embeds(batch_txt, model=model)
        else:
            emb = _sbert_embeds(batch_txt, model=(model or "all-MiniLM-L6-v2"))
        
        vs.upsert(ids=ids[st:ed], embs=emb, docs=docs[st:ed], metadatas=metas[st:ed])
        emb_count += len(batch_txt)

    s.vector_store_info = {"persist_dir": persist_dir, "collection_name": collection_name}
    s.embedded_count = emb_count
    s.indexed_ids = ids
    
    return s
