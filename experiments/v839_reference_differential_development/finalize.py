from pathlib import Path
import sys
own=Path(__file__).resolve().parent
sys.path.insert(0,str(own.parent/'reference_differential_20261106'))
from finalizer import finalize
finalize(own)
