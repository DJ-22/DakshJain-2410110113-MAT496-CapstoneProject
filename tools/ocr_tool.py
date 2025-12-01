from pypdf import PdfReader
from pathlib import Path

def ocr_file(path):
    """ 
    Perform OCR on the given file path.
    """
    
    p = Path(path)
    ext = p.suffix.lower()
    
    if ext == '.pdf':
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        
        return "\n".join(pages)
    else:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
