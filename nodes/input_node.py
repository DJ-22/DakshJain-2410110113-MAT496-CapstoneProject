from pathlib import Path
from state.input_state import State

def read_inputs(path='data'):
    """
    Read input files from the specified directory and update the state.
    """
    
    p = Path(path)
    files = [str(f) for f in p.iterdir() if f.is_file()]
    s = State()
    s.raw_files = files
    
    return s
