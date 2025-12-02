from typing import Any, Dict, Optional
import os
from langgraph.graph import StateGraph, END

try:
    from state.graph_state import GraphState, initialize_state as initialize_graph_state
    StateType = GraphState
    _have_typed = True
except Exception:
    from state.input_state import State as StateType
    initialize_graph_state = None
    _have_typed = False

from nodes.input_node import read_inputs
from nodes.ocr_node import run_ocr
from nodes.cleaning_node import clean_text
from nodes.extraction_node import run_extract
from nodes.embedding_node import run_embeddings
from nodes.retrieval_node import run_retrieval
from nodes.rag_node import run_rag
from nodes.budget_node import run_budget
from nodes.trend_node import build_trends
from nodes.chart_node import make_charts

def build_graph() -> StateGraph:
    """
    Build and compile the processing graph.
    """
    graph = StateGraph(StateType)

    graph.add_node("input", read_inputs)
    graph.add_node("ocr", run_ocr)
    graph.add_node("clean", clean_text)
    graph.add_node("extract", run_extract)
    graph.add_node("embed", run_embeddings)
    graph.add_node("retrieve", run_retrieval)
    graph.add_node("rag", run_rag)
    graph.add_node("budget", run_budget)
    graph.add_node("trend", build_trends)
    graph.add_node("chart", make_charts)

    graph.add_edge("input", "ocr")
    graph.add_edge("ocr", "clean")
    graph.add_edge("clean", "extract")
    graph.add_edge("extract", "embed")
    graph.add_edge("embed", "retrieve")
    graph.add_edge("retrieve", "rag")
    graph.add_edge("rag", "budget")
    graph.add_edge("budget", "trend")
    graph.add_edge("trend", "chart")
    graph.add_edge("chart", END)

    graph.set_entry_point("input")
    
    return graph.compile()


def run_finance_pipeline(data_dir: Optional[str] = "data",
                         enable_rag: bool = False,
                         rag_model: Optional[str] = None,
                         rag_top_k: int = 6) -> Dict[str, Any]:
    """
    Run the full financial document processing pipeline.
    """

    if initialize_graph_state is not None:
        state = initialize_graph_state(raw_files=None)
    else:
        state = StateType()

    try:
        if not getattr(state, "logs", None):
            state.logs = []
    except Exception:
        try:
            state["logs"] = []
        except Exception:
            pass

    def _log(m: str):
        """ 
        Helper to log to state logs.
        """
        
        try:
            if hasattr(state, "logs"):
                state.logs.append(m)
            else:
                state["logs"].append(m)
        except Exception:
            pass

    _log("pipeline:start")

    try:
        pre = read_inputs(data_dir)
        
        try:
            state.raw_files = getattr(pre, "raw_files", pre.raw_files if hasattr(pre, "raw_files") else pre.get("raw_files", []))
        except Exception:
            try:
                state["raw_files"] = pre.get("raw_files", [])
            except Exception:
                pass
        
        _log(f"input: discovered {len(getattr(state, 'raw_files', state.get('raw_files', []) if isinstance(state, dict) else []))} files")
    except Exception as e:
        _log(f"input node failed: {e}")

    graph = build_graph()
    final_state = graph.invoke(state)

    def _get(k, default=None):
        """ 
        Helper to get attribute or key from final state. 
        """
        
        try:
            return getattr(final_state, k)
        except Exception:
            try:
                return final_state.get(k, default)
            except Exception:
                return default

    report = {
        "ok": True,
        "files": _get("raw_files", []),
        "ocr_count": len(_get("ocr_output", {}) or {}),
        "extracted_count": _get("extracted_count", _get("extracted", []) and len(_get("extracted", [])) or 0),
        "embedded_count": _get("embedded_count", 0),
        "budget_results": _get("budget_results", {}),
        "chart_paths": _get("chart_paths", {}),
        "last_rag": _get("last_rag", {}) if enable_rag else {},
        "logs": _get("logs", []),
    }

    _log("pipeline:end")
    
    return report


def run_pipeline(data_dir: str = "data", 
                budget_cfg: Optional[Dict[str, float]] = None,
                use_llm: bool = True,
                query: Optional[str] = None,
                top_k: int = 3) -> GraphState:
    """
    Run the complete financial document processing pipeline step-by-step.
    """

    state = read_inputs(data_dir)
    print(f"[1] read_inputs -> files: {len(state.raw_files)}")

    state = run_ocr(state)
    print(f"[2] run_ocr -> ocr_output keys: {len(state.ocr_output)}")

    state = clean_text(state)
    print(f"[3] clean_text -> sms blocks: {len(state.clean_text.get('sms', []))}, bank blocks: {len(state.clean_text.get('bank', []))}")

    state = run_extract(state)
    print(f"[4] run_extract -> extracted_count: {state.extracted_count}")

    state = run_embeddings(state)
    print(f"[5] run_embeddings -> embedded_count: {state.embedded_count}")

    if query:
        res = run_retrieval(state, query, top_k=top_k)
        print(f"\n[6] Retrieval sample for query: '{query}' -> {len(res)} results")
        for r in res:
            m = r.get("meta", {})
            print(" -", m.get("txn_id"), "|", m.get("vendor"), "|", m.get("amount"))

    if use_llm and not os.getenv("OPENAI_API_KEY"):
        print("Warning: use_llm=True but OPENAI_API_KEY not found, setting use_llm=False")
        use_llm = False
    
    state = run_budget(state, budget_cfg=budget_cfg, use_llm=use_llm)

    state = build_trends(state)

    state = make_charts(state, out_dir="data/charts", top_n=5)
    
    return state
