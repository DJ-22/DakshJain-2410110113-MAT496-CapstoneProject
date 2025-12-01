class State:
    """ 
    Class to hold the state of input processing.
    """
    
    def __init__(self):
        self.raw_files = []
        self.ocr_output = {}
        self.clean_text = {}
