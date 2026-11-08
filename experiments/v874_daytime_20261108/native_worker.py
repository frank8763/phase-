"""Unchanged production physical engine; only fixed multi-route authority/manifest selection differs."""
import sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import authorized
import native_backend as engine
engine.C=C;engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
