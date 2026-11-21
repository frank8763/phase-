"""Keep original root/native caps; only one original current-event allowance."""
import importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
s=importlib.util.spec_from_file_location('v1471_scope_contract',C/'contract.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
read=contract.read;sha=contract.sha;clocks=contract.clocks;complete_admission=contract.complete_narrow_admission

def limits_check(limits):
 assert limits==read(C/'LIMITS.json')and limits['scope']==contract.SCOPE
 assert limits['maximum_completed_events']==1 and limits['repeat_or_pair_authorized']is False and limits['whole_route_admission']is False
 original=read(R/'experiments/v1456_route_closure_binding/LIMITS.json')
 expected=dict(original);expected.update(scope=contract.SCOPE,maximum_completed_events=1,repeat_or_pair_authorized=False,whole_route_admission=False,canonical_initializer_wall_cap_s=180,cooperative_native_stop_wall_s=200)
 expected['witness']=dict(original['witness'],maximum_events=1,maximum_generation_native=1005000,maximum_audit_native=1005000)
 assert limits==expected,'LIVE_EVENT_UNDECLARED_BUDGET_CHANGE'
 assert limits['maximum_actual_native']==40000 and limits['maximum_task_wall_s']==5400 and limits['witness']['maximum_nominal_native']==5000
 return True

def allocated(path):
 import subprocess
 return int(subprocess.check_output(['du','-sx','-B1',str(path)],text=True,timeout=10).split()[0])
def storage_preflight(limits):
 limits_check(limits);used=allocated(R/'runs');future=sum(limits[k]for k in ['maximum_task_evidence_bytes','archive_reserve_bytes','download_reserve_bytes','root_reserve_bytes'])
 assert used+future<limits['storage_limit_bytes'],'LIVE_EVENT_ALL_RUNS_EVIDENCE_ARCHIVE_DOWNLOAD_ROOT_PEAK'
 return dict(passed=True,allocated_all_runs_bytes=used,estimated_cap_peak_bytes=used+future,limit_bytes=limits['storage_limit_bytes'],inode_counted=True,models=0)
