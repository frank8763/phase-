"""Resource bootstrap BEFORE immutable guard; then the qualified new driver."""
import hashlib,json,os,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs'/C.name
assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
assert (O/'PILOT_ADMISSION.json').is_file(),'DWA_LIVE_COMPONENT_NOT_ADMITTED'
a=json.loads((O/'PILOT_ADMISSION.json').read_text())
assert a['models_authorized']and a['scope']=='DWA_FRESH_T0_ORIGINAL_ACTUATOR_COMPONENT'
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==a['pilot_entry_sha256']
source=json.loads((O/'SOURCE_FREEZE.json').read_text())['files']
p=R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()==source[str(p.relative_to(R))]
sys.path.insert(0,str(p.parent));import resource_policy
resource_policy.apply()
sys.path.insert(0,str(C))
runpy.run_path(str(C/'driver.py'),run_name='__main__')
