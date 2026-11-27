"""I/O-only exact closure of the V2168 owner failure before any child existed."""
from pathlib import Path
import os,sys,fcntl,json,hashlib,importlib.util,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;P=R/'runs/v2168_sccr_live_union';O=P/'components/SCCR'
sys.path.insert(0,str(R/'experiments/v2168_sccr_live_union'))
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def idle():
 handles=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 i=read(P/'LAUNCH_IDENTITY.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or Path('/proc/sys/kernel/random/boot_id').read_text().strip()!=i['boot_id']or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','PILOT_WINDOW.json','PILOT_ADMISSION.json','actual'])
 return handles
def review(rid):
 assert rid=='SCCR';handles=idle();console=P/'owner.console';text=console.read_text();assert 'FileNotFoundError'in text and 'COMPONENT_INTERFACE_PROOF.json'in text
 path=O/'RUNTIME_CLOSED_REVIEW.json'
 if path.exists():assert read(path)['owner_console_sha256']==sha(console);return
 assert not(O/'COMPLETION.json').exists()
 value=dict(closed=True,passed=False,closure_author='V2169_EXTERNAL_PRE_CHILD_RECONCILIATION_NOT_MACHINE_RESULT',first_error='FileNotFoundError: COMPONENT_INTERFACE_PROOF.json',secondary_errors=[],actual_native=None,own_replay_native=None,canonical_vehicle_initializations=None,internal_factory_model_constructions=None,whole_navigation_passed=False,formal_assignments_executed=0,machine_RESULT_missing=True,owner_pid_identity_gone=True,child_never_registered=True,PILOT_once_never_claimed=True,actual_directory_never_created=True,owner_console_sha256=sha(console),source_unchanged=True)
 dump(O/'COMPLETION.json',value)
 review=dict(value,owner_completion_sha256=sha(O/'COMPLETION.json'),machine_result_present=False,machine_result_sha256=None,machine_counts_remain_null=True,source_derived_counts_separate=dict(factory_attempts=0,explicit_renderer_constructors=0,explicit_actor_constructors=0,weight_loads=0,forward_calls=0,actual_native=0,replay_native=0),source_derived_count_basis='actual owner traceback and missing proof guard before actual.mkdir/PILOT claim/child Popen; no retry',independent_audit=None,learned_actor_accounting=None,total_modelwork=None,source_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),REVIEW_exact=True,global_locks_idle=True,late_recovery_helper_sha256=sha(Path(__file__)),new_numerical_or_model_calls=0)
 dump(path,review)
 snapshots=O/'LATE_IO_RECOVERY_HELPERS';snapshots.mkdir()
 for p in [Path(__file__),C/'PROTOCOL.md']:(snapshots/p.name).write_bytes(p.read_bytes())
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));stage=sys.argv[1]
 sp=importlib.util.spec_from_file_location('unchanged_v2168_transport_with_explicit_late_prechild_overlay',R/'experiments/v2168_sccr_live_union/evidence.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 m.idle_closed=idle;m.close_review=review
 if stage=='archive':review('SCCR');m.archive('SCCR')
 elif stage=='ref':m.ref('SCCR')
 elif stage=='deliver':raise SystemExit(m.deliver('SCCR'))
 elif stage=='barrier':m.barrier('SCCR')
 else:raise AssertionError('UNKNOWN_PRECHILD_CLOSURE_STAGE')
if __name__=='__main__':main()
