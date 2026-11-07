from pathlib import Path
import sys
own=Path(__file__).resolve().parent
sys.path.insert(0,str(own.parent/'overnight_recovery_20261105'))
from finalizer import finalize
finalize(own)
