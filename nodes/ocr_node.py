from pathlib import Path
from tools.ocr_tool import ocr_file
from state.input_state import State

def run_ocr(s: State):
    """ 
    Run OCR on all raw files in the State object. 
    """
    
    out = {}
    
    try:
        for f in getattr(s, "raw_files", []):
            try:
                ext = Path(f).suffix.lower()
                
                if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                    out[f] = ocr_file(f)
                else:
                    out[f] = Path(f).read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                out[f] = ""  
        
        s.ocr_output = out
    
    except Exception as e:
        s.ocr_output = out
    
    return s
