from pathlib import Path
import sys
own=Path(__file__).resolve().parent
sys.path.insert(0,str(own.parent/"dynamic_acceptance_20261105"))
from runner import run
run(own)
