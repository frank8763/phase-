"""Close one pre-numerical technical censor from exact original console/source only."""
import fcntl,hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';SOURCE=R/'runs/v1649_error_stop_sensor_capture';O=ROOT/'rounds/phase_03__full'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5})
 c=read(O/'COMPLETION.json');assert c['closed'] and not c['passed'] and c['review_restored'] and c['lock_idle'] and c['actual_native'] is None and c['own_replay_native'] is None and c['canonical_vehicle_initializations'] is None
 assert not(O/'actual/RESULT.json').exists()and not list((O/'actual').iterdir())
 ident=read(O/'OWNED_CHILD.json');p=Path('/proc')/str(ident['pid'])/'stat'
 if p.exists():assert p.read_text().split(') ',1)[1].split()[19]!=ident['start_ticks']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 console=(O/'formal.console').read_text();assert 'in admission' in console and "0<w['absolute_deadline_unix']-w['started_unix']<=5400"in console and console.rstrip().endswith('AssertionError')
 driver=(R/'experiments/v1649_error_stop_sensor_capture/driver.py').read_text();assert driver.index('authority,window,source,assignment=admission()')<driver.index("caches=load(")<driver.index('return execute(')
 context=(R/'experiments/v1649_error_stop_sensor_capture/context.py').read_text();assert "0<w['hard_stop_monotonic']-w['started_monotonic']<=5400" in context
 w=read(O/'ROUND_WINDOW.json');mono=w['hard_stop_monotonic']-w['started_monotonic'];wall=w['absolute_deadline_unix']-w['started_unix'];assert mono>5400 and mono<5400+1e-8 and wall==5400
 proof=dict(closed=True,passed=False,machine_RESULT_missing=True,canonical_owner_counts_preserved=dict(canonical_vehicle_initializations=None,actual_native=None,own_replay_native=None),source_derived_before_numerical_import=dict(canonical_factory_calls=0,model_calls=0,physical_native=0,replay_native=0),inference_scope='Exact original console and entry control flow, not reconstructed machine RESULT',console_path=str((O/'formal.console').relative_to(R)),console_sha256=sha(O/'formal.console'),original_owner_first_error=c['first_error'],native_entry_primary='AssertionError at immutable context.admission dual-clock duration bound',wall_duration_repr=repr(wall),monotonic_duration_repr=repr(mono),round_once_consumed=True,no_retry=True,all_source_SHA_verified_after_child_exit=True,source_members=len(frozen),review_original=True,execution_idle=True,owned_child_gone=True,recorded_unix=time.time(),source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [O/'COMPLETION.json',O/'ROUND_WINDOW.json',O/'formal.console',R/'experiments/v1649_error_stop_sensor_capture/context.py',R/'experiments/v1649_error_stop_sensor_capture/driver.py']})
 put(O/'CONSOLE_RECOVERED_FAILURE_RECORD.json',proof)
 review=dict(proof,formal_assignment_id='phase_03__full',original_contract=True,actual_native=None,own_replay_native=None,canonical_initializations=None,internal_factory_model_constructions=None,full_modelwork_total=None,independent_full_goal_audit=None,independent_prefix_safety_audit=None,actual_original_goal_reached=None,scientific_classification='TECHNICAL_CENSOR_BEFORE_NUMERICAL_ADMISSION',first_error=proof['native_entry_primary'],outer_first_error=c['first_error'],remote_runtime_recovery_pending=True)
 put(O/'RUNTIME_CLOSED_REVIEW.json',review)
 ledger=read(ROOT/'FORMAL_LEDGER.json');row=next(x for x in ledger['rows']if x['assignment_id']=='phase_03__full');row.update(registered=True,closed=True,status='CLOSED_TECHNICAL_CENSOR_RECOVERY_PENDING',model_result=False,owner_passed=False,actual_native=None,own_replay_native=None,source_derived_physical_native=0,source_derived_replay_native=0,source_derived_canonical_factory_calls=0,scientific_classification='TECHNICAL_CENSOR_BEFORE_NUMERICAL_ADMISSION',completion_path=str((O/'COMPLETION.json').relative_to(R)),completion_sha256=sha(O/'COMPLETION.json'),source_version_root=str(SOURCE.relative_to(R)),independent_full_goal_audit_passed=False)
 ledger.update(registered_assignments=6,closed_assignments=6,unexecuted_assignments=14,recorded_unix=time.time());(ROOT/'FORMAL_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
 print(json.dumps({k:proof[k]for k in ['machine_RESULT_missing','source_derived_before_numerical_import','monotonic_duration_repr']}))
if __name__=='__main__':main()
