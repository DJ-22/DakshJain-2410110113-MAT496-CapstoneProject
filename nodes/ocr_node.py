from pathlib import Path
from tools.ocr_tool import ocr_file
from state.input_state import State

def run_ocr(s: State):
    """
    Run OCR on the raw files and update the state with the OCR output.
    """
    
    out = {}
    
    for f in s.raw_files:
        ext = Path(f).suffix.lower()
        if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
            out[f] = ocr_file(f)
        else:
            out[f] = Path(f).read_text(encoding='utf-8',errors='ignore')
    
    s.ocr_output = out
    
    return s
