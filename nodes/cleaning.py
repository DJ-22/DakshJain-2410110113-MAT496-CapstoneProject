import re

class CleaningNode:
    """
    Node to clean text by removing long dashed lines and collapsing large whitespace blocks.
    """
    
    def run(self, text):
        text = re.sub(r"-{3,}", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return {"clean_text": text}
