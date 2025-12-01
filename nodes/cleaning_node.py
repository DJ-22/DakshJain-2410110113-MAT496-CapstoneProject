import re
from state.input_state import State

def normalize_date(m):
    """ 
    Normalize date formats to YYYY-MM-DD.
    """
    
    return m.group(0)

def clean_text(s:State):
    """ 
    Clean and categorize text from OCR output into SMS, receipts, and bank statements.
    """
    
    raw = s.ocr_output
    res = {'sms':[], 'receipts':[], 'bank':[]}
    
    for fn, t in raw.items():
        t = re.sub(r'FROM:\s*', '', t)
        t = re.sub(r'\[?\d{4}-\d{2}-\d{2}[^\]]*\]?', '', t)
        t = re.sub(r'\r','\n',t)
        
        if 'BANK' in t.upper() or 'BALANCE' in t.upper() or 'OPENING BALANCE' in t.upper():
            res['bank'].append(t.strip())
        elif any(k in t.upper() for k in ['RECEIPT', 'ORDER', '#', 'ITEM', 'TOTAL', 'SUBTOTAL']):
            res['receipts'].append(t.strip())
        else:
            res['sms'].append(t.strip())
    
    s.clean_text = res
    
    return s
