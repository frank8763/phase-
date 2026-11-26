"""Resource bootstrap BEFORE immutable guard; then the qualified new driver."""
import hashlib,json,os,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs/v2037_parallel_reserved_source/lanes'/'common_09__RPP'
assert (O/'PILOT_ADMISSION.json').is_file(),'RPP_COMPONENT_NOT_ADMITTED'
assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
a=json.loads((O/'PILOT_ADMISSION.json').read_text())
assert a['models_authorized']and a['scope']=='RPP_CURRENT_COMMON_FULL_TASK'
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==a['pilot_entry_sha256']
source=json.loads((O/'SOURCE_FREEZE.json').read_text())['files']
sys.path.insert(0,str(C));import cpu_policy
cpu_policy.install()
sys.path.insert(0,str(C))
runpy.run_path(str(C/'driver.py'),run_name='__main__')
