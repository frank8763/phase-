"""Standalone entry; authority is checked before lazy physical imports."""
import sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import authorized
import native_loop as engine
engine.C=C;engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
