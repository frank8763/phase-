"""IO-only fixed snapshot, not a model-run baseline or budget expansion."""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name
def admission():
 own=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert own+(32+8+512)*1024**2<16106127360
 return dict(passed=True,joint_peak_bytes=16106127360,actual_all_runs_bytes=own,models=0)
def transport_current_upper():
 p=S/'IO_ADMISSION.json';b=json.loads(p.read_text());assert b['passed']and b['actual_all_runs_bytes']+(32+8+512)*1024**2<16106127360
 return b['actual_all_runs_bytes']+8*1024**2
