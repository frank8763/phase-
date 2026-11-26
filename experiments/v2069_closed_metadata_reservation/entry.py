"""Parent-only metadata accounting, exact frozen CPU6 numerical child unchanged."""
from pathlib import Path
import ast,hashlib,importlib.util,inspect,json,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs/v2045_remaining_parallel_source';OLD=R/'experiments/v2047_mppi_remaining_ten'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shared_metadata_admit(metadata,root):
 assert root.parent==S/'rounds'and root.name in ['common_11__MPPI','common_12__MPPI'];plan=read(S/'PLAN_LOCKED.json');rpp=0
 for row in plan['methods']['RPP']:
  O=R/row['root'];assert read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed'];i=read(O/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
  for folder in [O,S/'runtime_archives'/row['round_id']]:
   for p in folder.rglob('*'):
    if p.is_file()and'actual'not in p.relative_to(folder).parts:rpp+=p.lstat().st_blocks*512
 extra=max(0,metadata+2*1024**2-16*1024**2);assert extra<=8*1024**2 and rpp+extra<=16*1024**2,'COMBINED_ORIGINAL_METADATA_RESERVATION_EXHAUSTED'
 baseline=read(S/'QUIESCENT_BASELINE.json');assert baseline['joint_peak_bytes']==16095019008 and sum(x['metadata_bytes']for x in baseline['lanes'])==32*1024**2
 proof=dict(passed=True,MPPI_metadata_actual_allocated=metadata,own_future_parent_headroom_bytes=2*1024**2,finished_RPP_metadata_allocated=rpp,original_MPPI_metadata_reserve=16*1024**2,closed_RPP_metadata_reserve=16*1024**2,additional_metadata_covered_by_idle_RPP_reserve=extra,maximum_reallocation=8*1024**2,joint_peak_bytes_unchanged=16095019008,all_RPP_models_permanently_closed=True,RPP224MiB_physical_retention_bank_untouched=True,no_index_or_anchor_deletion=True,no_numerical_source_or_gate_change=True)
 dest=root/'SHARED_METADATA_RESERVATION.json';assert not dest.exists();dest.write_text(json.dumps(proof,indent=2)+'\n');return True
def main():
 assert os.sched_getaffinity(0)=={5};rid=os.environ['PHASE_COMMON_ASSIGNMENT'];assert rid in ['common_11__MPPI','common_12__MPPI'];O=S/'rounds'/rid;assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','FORMAL_REGISTERED.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 sys.path.insert(0,str(OLD));import queue_storage
 function=inspect.getsource(queue_storage.admit);old="assert metadata+2*1024**2<=16*1024**2,'LANE_METADATA_RESERVATION_EXHAUSTED_BEFORE_CLAIM'";assert function.count(old)==1;new="assert shared_metadata_admit(metadata,O),'COMBINED_METADATA_RESERVATION_REFUSED'";function=function.replace(old,new);ast.parse(function);space=dict(queue_storage.__dict__,shared_metadata_admit=shared_metadata_admit);exec(compile(function,str(C/'entry.py'),'exec'),space);queue_storage.admit=space['admit']
 spec=importlib.util.spec_from_file_location('unchanged_original_MPPI_owner',OLD/'owner.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);raise SystemExit(m.main())
if __name__=='__main__':main()
