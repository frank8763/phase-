"""Resource bootstrap BEFORE immutable guard; then the qualified new driver."""
import hashlib,json,os,runpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs/v2045_remaining_parallel_source';RID=os.environ.get('PHASE_COMMON_ASSIGNMENT','common_03__MPPI');assert RID in ['common_03__MPPI', 'common_04__MPPI', 'common_05__MPPI', 'common_06__MPPI', 'common_07__MPPI', 'common_08__MPPI', 'common_09__MPPI', 'common_10__MPPI', 'common_11__MPPI', 'common_12__MPPI'];O=SOURCE/'rounds'/RID
assert (O/'PILOT_ADMISSION.json').is_file(),'MPPI_COMPONENT_NOT_ADMITTED'
assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[6]
a=json.loads((O/'PILOT_ADMISSION.json').read_text())
assert a['models_authorized']and a['scope']=='MPPI_CURRENT_COMMON_FULL_TASK'
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==a['pilot_entry_sha256']
source=json.loads((SOURCE/'SOURCE_FREEZE.json').read_text())['files']
sys.path.insert(0,str(C));import cpu_policy
cpu_policy.install()
sys.path.insert(0,str(C))
runpy.run_path(str(C/'driver.py'),run_name='__main__')
