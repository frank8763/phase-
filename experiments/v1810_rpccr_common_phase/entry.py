"""Resource bootstrap BEFORE immutable guard; then the qualified new driver."""
import hashlib,json,os,runpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import C,O,R,ROOT,SOURCE,read,sha
assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
assert O!=SOURCE and(O/'FORMAL_ADMISSION.json').is_file(),'REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED'
a=read(O/'FORMAL_ADMISSION.json')
assert a['models_authorized']and a['scope']=='ORIGINAL_V1281_WE_PHASE_COMPARISON'
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==a['entry_sha256']
source=json.loads((SOURCE/'SOURCE_FREEZE.json').read_text())['files']
p=R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()==source[str(p.relative_to(R))]
sys.path.insert(0,str(p.parent));import resource_policy
resource_policy.apply()
sys.path.insert(0,str(C))
runpy.run_path(str(C/'driver.py'),run_name='__main__')
