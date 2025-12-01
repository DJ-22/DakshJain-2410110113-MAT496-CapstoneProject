import re
from pathlib import Path
from pypdf import PdfReader
from state.input_state import State
from typing import List, Dict, Optional
from tools.validator import validate

_DATE_RE_GENERIC = re.compile(
    r'(\d{4}-\d{2}-\d{2})|(\d{2}-[A-Za-z]{3}-\d{4})|(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    re.IGNORECASE,
)
_SMS_MSG_RE = re.compile(r'(\[\d{4}-\d{2}-\d{2}[^]]*\].*?)(?=(\[\d{4}-\d{2}-\d{2})|$)', re.S)
_BANK_ROW_RE = re.compile(r'^\s*(\d{2}-[A-Za-z]{3}-\d{4})\s*\|\s*(.+)$', re.MULTILINE)
_AMOUNT_RE = re.compile(
    r'(?:(?:[$₹£€])\s*\d{1,3}(?:[,0-9]{3})*(?:\.\d{2})?)|(?:\d+\.\d{2})'
)
_CURRENCY_SYMS = {'$': 'USD', '₹': 'INR', '£': 'GBP', '€': 'EUR'}

def _month_to_num(mon_str: str) -> int:
    """ 
    Convert 3-letter month abbreviation to month number.
    """
    
    ms = mon_str[:3].lower()
    mapping = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    
    return mapping.get(ms, 0)

def _normalize_date_token(tok: str) -> Optional[str]:
    """
    Normalize various date formats to YYYY-MM-DD.
    """
    
    if not tok:
        return None
    
    tok = tok.strip()
    m = re.match(r'^\d{4}-\d{2}-\d{2}$', tok)
    if m:
        return tok

    m = re.match(r'^(\d{2})-([A-Za-z]{3})-(\d{4})$', tok)
    if m:
        d, mon, y = m.groups()
        monn = _month_to_num(mon)
        if monn:
            return f'{int(y):04d}-{monn:02d}-{int(d):02d}'

    m = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$', tok)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2:
            y = '20' + y
        
        return f'{int(y):04d}-{int(mo):02d}-{int(d):02d}'

    m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})', tok, re.I)
    if m:
        mon_str, d, y = m.groups()
        monn = _month_to_num(mon_str)
        
        return f'{int(y):04d}-{monn:02d}-{int(d):02d}'
    
    return None

def _clean_number_token(tok: str) -> Optional[float]:
    """
    Clean a money token string to extract float value.
    """
    
    if not tok:
        return None
    
    t = tok.strip()
    t2 = re.sub(r'[^\d\.\-]', '', t)
    if not t2:
        return None
    
    try:
        return float(t2)
    except Exception:
        return None

def _guess_currency(text: str) -> Optional[str]:
    """ 
    Guess currency code from text based on symbols or keywords.
    """
    
    for s, code in _CURRENCY_SYMS.items():
        if s in text:
            return code

    if re.search(r'\bINR\b', text, re.I): 
        return 'INR'
    if re.search(r'\bUSD\b', text, re.I): 
        return 'USD'
    
    return None

def _parse_bank_row(line: str) -> Optional[Dict]:
    """
    Parse a single bank statement row line.
    """

    cols = [c.strip() for c in line.split('|')]
    if len(cols) < 2:
        return None
    
    date_tok = cols[0]
    date = _normalize_date_token(date_tok)
    desc = cols[1] if len(cols) > 1 else None
    debit = credit = None
    
    for c in cols[2:]:
        if not c:
            continue

        amt_match = _AMOUNT_RE.search(c)
        if not amt_match:
            num_match = re.search(r'[\d,]+\.\d{2}', c)
            if num_match:
                val = _clean_number_token(num_match.group(0))

                if re.search(r'cr|credit|\+', c, re.I):
                    credit = val
                else:
                    debit = val
            
            continue
        
        val = _clean_number_token(amt_match.group(0))
        if re.search(r'cr\b|credit|\+', c, re.I):
            credit = val
        else:
            debit = val

    amount = None
    if debit is not None:
        amount = debit
    elif credit is not None:
        amount = credit
    else:
        m = _AMOUNT_RE.search(line)
        if m:
            amount = _clean_number_token(m.group(0))

    currency = _guess_currency(line) or 'USD'  

    return {
        "date": date,
        "vendor": desc if desc else None,
        "amount": amount,
        "currency": currency,
        "desc": line.strip(),
        "source": "bank"
    }

def _parse_sms_message(msg: str) -> Optional[Dict]:
    """
    Parse a single SMS message text.
    """
    
    if not msg or not msg.strip():
        return None
    
    text = msg.strip()
    m = re.match(r'^\[(\d{4}-\d{2}-\d{2})[^\]]*\]\s*(.*)$', text, re.S)
    date = None
    body = text
    
    if m:
        date = _normalize_date_token(m.group(1))
        body = m.group(2).strip()
    if not re.search(r'\b(debit|paid|payment|charge|credited|withdrawn|transfer|spent|purchase|order total|total|fare|bill|deducted)\b', body, re.I):
        return None

    money_iter = list(re.finditer(_AMOUNT_RE, body))
    amount = None
    currency = None
    
    for mm in money_iter:
        span_start, span_end = mm.span()
        context = body[max(0, span_start-10): min(len(body), span_end+10)].lower()
        
        if 'bal' in context or 'balance' in context:
            continue
        
        amount = _clean_number_token(mm.group(0))
        currency = _guess_currency(mm.group(0))
        
        break

    if amount is None and money_iter:
        amount = _clean_number_token(money_iter[0].group(0))
        currency = _guess_currency(money_iter[0].group(0))
    if amount is None:
        return None

    vendor = None
    for kw in (r'\bto\s+([A-Za-z0-9_\'\-\.\s&]+)', r'\bat\s+([A-Za-z0-9_\'\-\.\s&]+)', r'\bfor\s+([A-Za-z0-9_\'\-\.\s&]+)', r'\bvia\s+([A-Za-z0-9_\'\-\.\s&]+)'):
        mm = re.search(kw, body, re.I)
        if mm:
            vendor = mm.group(1).strip(" .,-")
            break
    
    if not vendor:
        mm = re.search(r'from[:\s]+([A-Za-z0-9_\'\-\.\s&]+)', text, re.I)
        if mm:
            vendor = mm.group(1).strip(" .,-")

    return {
        "date": date,
        "vendor": vendor if vendor else None,
        "amount": amount,
        "currency": currency if currency else 'USD',
        "desc": body if len(body) < 2000 else body[:2000] + '...',
        "source": "sms"
    }

def run_extract(s: State) -> State:
    """
    Extract structured transaction data from OCR output text.
    """
    
    extracted: List[Dict] = []
    ocr_out = getattr(s, 'ocr_output', {}) or {}

    for fn, txt in ocr_out.items():
        if not isinstance(txt, str):
            txt = str(txt or '')

        p = Path(fn)
        if p.suffix.lower() == '.pdf':
            try:
                reader = PdfReader(str(p))
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    page_text = page_text.strip()
                    
                    if not page_text:
                        continue

                    rows = re.findall(_BANK_ROW_RE, page_text)
                    if rows:
                        for match in re.finditer(r'^\s*\d{2}-[A-Za-z]{3}-\d{4}.*$', page_text, re.MULTILINE):
                            row_line = match.group(0)
                            parsed = _parse_bank_row(row_line)
                            
                            if parsed and validate(parsed):
                                parsed['file'] = fn
                                parsed['page'] = i+1
                                extracted.append(parsed)
                        
                        continue

                    msgs = re.findall(_SMS_MSG_RE, page_text)
                    if msgs:
                        for tup in msgs:
                            msg = tup[0]
                            parsed = _parse_sms_message(msg)
                            
                            if parsed and validate(parsed):
                                parsed['file'] = fn
                                parsed['page'] = i+1
                                extracted.append(parsed)
                        
                        continue

                    parsed = _parse_bank_row(page_text) or _parse_sms_message(page_text)
                    if parsed and validate(parsed):
                        parsed['file'] = fn
                        parsed['page'] = i+1
                        extracted.append(parsed)
                
                continue
            except Exception:
                pass

        fname_lower = fn.lower()
        if 'sms' in fname_lower or 'msg' in fname_lower:
            msgs = [m[0] for m in re.findall(_SMS_MSG_RE, txt)]
            if not msgs:
                msgs = [b.strip() for b in re.split(r'\n\s*\n', txt) if b.strip()]
            for msg in msgs:
                parsed = _parse_sms_message(msg)
                if parsed and validate(parsed):
                    parsed['file'] = fn
                    parsed['page'] = None
                    extracted.append(parsed)
            
            continue

        rows = [m.group(0) for m in re.finditer(r'^\s*\d{2}-[A-Za-z]{3}-\d{4}.*$', txt, re.MULTILINE)]
        if rows:
            for row in rows:
                parsed = _parse_bank_row(row)
                if parsed and validate(parsed):
                    parsed['file'] = fn
                    parsed['page'] = None
                    extracted.append(parsed)

            continue

        chunks = [b.strip() for b in re.split(r'\n\s*\n', txt) if b.strip()]
        for ch in chunks:
            parsed = _parse_bank_row(ch) or _parse_sms_message(ch)
            if parsed and validate(parsed):
                parsed['file'] = fn
                parsed['page'] = None
                extracted.append(parsed)

    s.extracted = extracted
    s.extracted_count = len(extracted)
    
    return s
