# state/graph_state.py
from typing import List, Dict, Any, Optional

class GraphState:
    # basic inputs
    raw_files: List[str]
    # OCR and cleaned text
    ocr_output: Dict[str, str]
    clean_text: Dict[str, List[str]]       # {"sms":[...], "bank":[...]}
    # extraction
    extracted: List[Dict[str, Any]]
    extracted_count: int
    # embeddings/index
    indexed_ids: List[str]
    embedded_count: int
    vector_store_info: Dict[str, Any]
    # retrieval/rag
    last_query: Optional[Dict[str, Any]]
    last_rag: Optional[Dict[str, Any]]
    # budget / trend / charts
    budget_config_used: Dict[str, float]
    budget_results: Dict[str, Any]
    budget_category_map: Dict[str, List[str]]
    budget_vendor_map: Dict[str, str]
    trend_data: Dict[str, Any]
    chart_paths: Dict[str, str]
    # meta / debugging
    logs: List[str]

    def __init__(self):
        self.raw_files = []
        self.ocr_output = {}
        self.clean_text = {}
        self.extracted = []
        self.extracted_count = 0
        self.indexed_ids = []
        self.embedded_count = 0
        self.vector_store_info = {}
        self.last_query = None
        self.last_rag = None
        self.budget_config_used = {}
        self.budget_results = {}
        self.budget_category_map = {}
        self.budget_vendor_map = {}
        self.trend_data = {}
        self.chart_paths = {}
        self.logs = []

    def log(self, msg: str):
        self.logs.append(msg)
