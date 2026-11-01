"""Initialization-only correction: allow original factory to create its own output."""
import os,sys
from pathlib import Path
src=Path(os.environ['PHASE_REPO'])/'experiments/v694_discovery_execution_recovery/probe_initial.py'
sys.path.insert(0,str(src.parent))
source=src.read_text().replace("out=root/'fixed73';out.mkdir()","out=root/'fixed73_setup_final'")
exec(compile(source,str(src),'exec'))
