from typing import TypedDict, Optional, Dict, List, Any


class GraphState(TypedDict, total=False):
    """
    Central state object passed between LangGraph nodes.
    """

    raw_files: List[str]                   
    claim: Optional[str]                   
    context: Optional[str]                   

    ocr_output: Dict[str, str]             
    clean_text: Dict[str, List[str]]        

    extracted: List[Dict[str, Any]]        
    extracted_count: int

    indexed_ids: List[str]                  
    embedded_count: int
    vector_store_info: Dict[str, Any]     

    last_query: Dict[str, Any]           
    last_rag: Dict[str, Any]               
    retrieved_docs: List[Dict[str, Any]]    

    budget_config_used: Dict[str, float]     
    budget_results: Dict[str, Any]           
    budget_category_map: Dict[str, List[str]]#
    budget_vendor_map: Dict[str, str]        
    budget_report: Optional[str]             
    budget_recommendations: List[str]       

    trend_data: Dict[str, Any]              
    chart_paths: Dict[str, str]             

    logs: List[str]                          
    extra: Dict[str, Any]                    


def initialize_state(raw_files: Optional[List[str]] = None,
                     claim: Optional[str] = None,
                     context: Optional[str] = None) -> GraphState:
    """
    Initialize a GraphState with default values.
    """
    
    return GraphState({
        "raw_files": raw_files or [],
        "claim": claim,
        "context": context,
        "ocr_output": {},
        "clean_text": {"sms": [], "bank": []},
        "extracted": [],
        "extracted_count": 0,
        "indexed_ids": [],
        "embedded_count": 0,
        "vector_store_info": {},
        "last_query": {},
        "last_rag": {},
        "retrieved_docs": [],
        "budget_config_used": {},
        "budget_results": {},
        "budget_category_map": {},
        "budget_vendor_map": {},
        "budget_report": None,
        "budget_recommendations": [],
        "trend_data": {},
        "chart_paths": {},
        "logs": [],
        "extra": {},
    })
