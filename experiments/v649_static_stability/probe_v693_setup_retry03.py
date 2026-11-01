"""Setup-only retry: original source, fixed course env and separate output path."""
import os,sys
from pathlib import Path
os.environ['PHASE_COURSE_DISTANCE']='8'
os.environ['PHASE_COURSE_PHASE']='0'
src=Path(os.environ['PHASE_REPO'])/'experiments/v693_discovery_renewal_preview/probe_initial.py'
sys.path.insert(0,str(src.parent))
source=src.read_text().replace("root/'fixed73'","root/'fixed73_retry03'")
exec(compile(source,str(src),'exec'))
