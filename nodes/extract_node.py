import os
import json
import re
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

load_dotenv()
from openai import OpenAI

client = OpenAI() 

SCHEMA_PATH = "schema/transaction_schema.json"
PROMPT_PATH = "prompts/extract_txn_prompt.txt"


def _load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_prompt(raw_text):
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    return template.replace("{raw_text}", raw_text)


def _normalize_amount(a, raw_text):
    if a is None:
        return None
    if isinstance(a, (int, float)):
        return float(a)

    s = str(a)
    if "(" in s and ")" in s:
        s = "-" + s.replace("(", "").replace(")", "")

    s = s.replace("$", "").replace("USD", "").replace("usd", "")
    s = s.replace(",", "").strip()

    debit_indicators = ["debited", "paid", "withdrawn", "purchase", "spent"]
    if any(k in raw_text.lower() for k in debit_indicators) and not s.startswith("-"):
        m = re.search(r"-?\d+(\.\d+)?", s)
        if m:
            try:
                return -abs(float(m.group(0)))
            except:
                pass

    try:
        return float(s)
    except:
        m = re.search(r"-?\d+(\.\d+)?", s)
        return float(m.group(0)) if m else None


class ExtractNode:
    """ 
    Node to extract financial transactions from raw text using OpenAI's API.
    """
    
    def run(self, raw_text, model="gpt-4.1-mini", max_tokens=800):
        prompt = _load_prompt(raw_text)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=max_tokens,
        )

        try:
            content = resp.choices[0].message.content.strip()
        except Exception:
            content = json.dumps(resp, default=str)

        data = None
        try:
            data = json.loads(content)
        except Exception:
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end != 0:
                try:
                    data = json.loads(content[start:end])
                except Exception:
                    data = []
            else:
                data = []

        schema = _load_schema()
        final = []
        for obj in data:
            if not isinstance(obj, dict):
                continue

            obj.setdefault("currency", "USD")
            obj.setdefault("type", "unknown")
            if "amount" in obj:
                try:
                    obj["amount"] = _normalize_amount(obj["amount"], raw_text)
                except Exception:
                    obj["amount"] = None

            if "amount" not in obj or obj.get("amount") is None:
                m = re.search(r"\$?(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)", obj.get("description", "") or raw_text)
                if m:
                    try:
                        obj["amount"] = _normalize_amount(m.group(1), raw_text)
                    except:
                        pass

            if "date" in obj and isinstance(obj["date"], str):
                m = re.search(r"20\d{2}-\d{2}-\d{2}", obj["date"])
                if m:
                    obj["date"] = m.group(0)

            try:
                validate(instance=obj, schema=schema)
                final.append(obj)
            except ValidationError:
                try:
                    if "amount" in obj and obj["amount"] is not None:
                        obj["amount"] = float(obj["amount"])
                    validate(instance=obj, schema=schema)
                    final.append(obj)
                except Exception:
                    continue

        return {"transactions": final}
