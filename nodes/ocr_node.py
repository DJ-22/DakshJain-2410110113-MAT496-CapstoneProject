import pytesseract
from PIL import Image
import pdf2image

class OCRNode:
    """
    Node to perform OCR on PDF files.
    """
    
    def run(self, pdf_path):
        pages = pdf2image.convert_from_path(pdf_path)
        text = ""

        for p in pages:
            text += pytesseract.image_to_string(p)

        return {"ocr_text": text}
