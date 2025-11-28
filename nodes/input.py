class InputNode:
    """
    Node to handle input files of different types.
    """
    
    def run(self, file_path):
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return {"raw_text": f.read()}

        elif file_path.endswith(".pdf"):
            return {"raw_pdf_path": file_path}

        else:
            return {"error": "Unsupported file type"}
