from nodes.extract_node import ExtractNode

def test_usd_extraction():
    raw = """
    2025-09-05 $250 debited at Starbucks using Venmo
    2025-09-10 Salary credited $50000 from Employer Bank
    """
    e = ExtractNode()
    out = e.run(raw_text=raw, model="gpt-4.1-mini")

    assert "transactions" in out
    assert len(out["transactions"]) >= 1

    t0 = out["transactions"][0]
    assert t0["currency"] == "USD"
    assert isinstance(t0["amount"], float)
