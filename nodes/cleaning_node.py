import re
from pathlib import Path
from state.input_state import State

_ts_re = re.compile(r'\[\d{4}-\d{2}-\d{2}[^]]*\]')
_sms_like_re = re.compile(
    r'(BankAlert|Debit|Credit|Credited|Debited|Acct|A/c|account|OTP|ending in|IMPS|UPI|NEFT|\d{10,})',
    re.I
)
_bank_like_re = re.compile(
    r'(BALANCE|BAL:|AVAIL|WITHDRAWAL|DEPOSIT|CREDITED|DEBITED|IMPS|NEFT|UPI|POS|ATM|REF NO|A/C)',
    re.I
)

def _split_blocks(txt):
    """
    Split text into blocks separated by blank lines.
    """
    
    return [p.strip() for p in re.split(r'\n\s*\n', txt) if p.strip()]

def clean_text(s: State):
    """ 
    Clean and categorize OCR output text in the State object.
    """
    
    raw = getattr(s, "ocr_output", {}) or {}
    res = {"sms": [], "bank": []}

    for fn, txt in raw.items():
        if not isinstance(txt, str):
            txt = str(txt or '')
        
        txt = txt.replace('\r', '')
        name = Path(fn).name.lower()

        if 'sms' in name:
            for b in _split_blocks(txt):
                if _sms_like_re.search(b) or _ts_re.search(b):
                    res['sms'].append(b)
           
            continue

        if 'bank' in name:
            for b in _split_blocks(txt):
                if _bank_like_re.search(b):
                    res['bank'].append(b)
            
            continue

        for b in _split_blocks(txt):
            if _sms_like_re.search(b) or _ts_re.search(b):
                res['sms'].append(b)
            elif _bank_like_re.search(b):
                res['bank'].append(b)

    s.clean_text = res
    
    return s
