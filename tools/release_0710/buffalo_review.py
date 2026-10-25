from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
from buffalo_runner import *
execute(ROOT/'tools/release_079/review_art.py')
