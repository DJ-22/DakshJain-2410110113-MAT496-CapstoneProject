import os
from typing import List, Dict, Any
from state.input_state import State
from .vector_db_node import VectorStore
from .embedding_node import _openai_embeds, _sbert_embeds

try:
    import openai
except Exception:
    openai = None

def _query_emb(query: str, use_openai: bool = False, model: str = None):
    """ 
    Get embedding for a query string using specified model.
    """
    
    if use_openai:
        if openai is None:
            raise RuntimeError("openai package not available")
        
        return _openai_embeds([query], model=model)[0]
    
    return _sbert_embeds([query], model=(model or "all-MiniLM-L6-v2"))[0]

def run_retrieval(s: State, query: str, top_k: int = 5, persist_dir: str = "data/vectorstore",
                  collection_name: str = "transactions", model: str = None) -> List[Dict[str, Any]]:
    """
    Run retrieval on the vector store using a query string.
    
    """
    vs = VectorStore(persist_dir=persist_dir, collection_name=collection_name)
    use_openai = bool(openai is not None and os.getenv("OPENAI_API_KEY") and model and model.startswith("text-"))
    emb = _query_emb(query, use_openai=use_openai, model=model)
    res = vs.query_by_embedding(emb, n_results=top_k)
    s.last_query = {"query": query, "results_count": len(res)}
    
    return res
