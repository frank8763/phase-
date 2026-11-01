"""Setup-only retry: original source, fixed course env and separate output path."""
import os
from pathlib import Path
os.environ['PHASE_COURSE_DISTANCE']='8'
os.environ['PHASE_COURSE_PHASE']='0'
src=Path(os.environ['PHASE_REPO'])/'experiments/v693_discovery_renewal_preview/probe_initial.py'
source=src.read_text().replace("root/'fixed73'","root/'fixed73_retry02'")
exec(compile(source,str(src),'exec'))
