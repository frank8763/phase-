"""Logging-only continuation of the original locked V652 list and deadline."""
import datetime, fcntl, gzip, hashlib, json, os, signal, subprocess, time, traceback
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];src=Path(__file__).parent;root=repo/'runs/v653_static_log_recovery';prior_root=repo/'runs/v652_static_confirmation';prior=prior_root/'confirmation_window01'
def read(p):return json.loads(p.read_text())if p.exists()else None
def dump(p,j):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert read(prior/'COMPLETION.json')['status']=='GATE_FAILED_PHYSICAL_SOURCE_OR_SCENE_AUDIT'
window=root/'continuation01';window.mkdir()
origin=read(prior/'WINDOW.json');limit=origin['limit_s'];start=time.monotonic()-(time.time()-origin['started_unix'])
freeze={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(src.glob('*.py'))};protocol_hash=hashlib.sha256((src/'PROTOCOL.md').read_bytes()).hexdigest()
dump(window/'SOURCE_FREEZE.json',freeze);dump(window/'WINDOW.json',{'started_unix':time.time(),'original_started_unix':origin['started_unix'],'absolute_deadline_unix':origin['absolute_deadline_unix'],'limit_s':limit,'shared_original_budget':True,'pid':os.getpid()});(window/'PROTOCOL.md').write_bytes((src/'PROTOCOL.md').read_bytes())
proof=read(root/'DECISION_EQUIVALENCE.json');assert proof['equivalent'];assert proof['restored_original_runner_sha256']==read(prior/'SOURCE_FREEZE.json')['run_static.py']
selection=read(prior/'SELECTION_FREEZE.json');tasks=selection['tasks'];outcomes=read(prior/'CONFIRMATION_RESULTS.json');assert len(outcomes)==5 and sum(x['strict_success']for x in outcomes)==4 and outcomes[-1]['seed']==94000040 and outcomes[-1]['result']is None
for x in outcomes:x['run_root']='runs/v652_static_confirmation'
physical=read(prior_root/'FINAL_PHYSICAL_AUDITS.json');assert len(physical)==4 and all(x['passed']for x in physical)
for x in physical:x['run_root']='runs/v652_static_confirmation'
old_pair=prior_root/outcomes[-1]['name']/'paired';interrupted=read(old_pair/'geometry_memory/interrupted.json');native=read(old_pair/'NATIVE_REPLAY_AUDIT.json');assert interrupted['public_steps']==19 and interrupted['physics_steps']==152
h=hashlib.sha256()
with gzip.open(old_pair/'geometry_memory/contacts.jsonl.gz','rb')as stream:
 for b in iter(lambda:stream.read(1048576),b''):h.update(b)
assert h.hexdigest()==interrupted['contacts']['contact_log_content_sha256']
assert native['status']=='MATCHED_RECORDED_PUBLIC_STATES'and native['replay_integration_steps']==152 and native['maximum_full_public_qpos_error']<=1e-8 and native['maximum_full_public_qvel_error']<=1e-8 and native['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15 and native['reconstructed_native_states_below_015']==0 and native['replay_obstacle_contact_records']==0 and native['minimum_reconstructed_self_domain_margin_m']>=0
assert all(interrupted['contacts'][k]==0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records'])
physical.append({'name':outcomes[-1]['name'],'run_root':'runs/v652_static_confirmation','passed':True,'scope':'only the actually executed interrupted prefix; task remains a non-success','replay':native,'contact_digest_verified':True});outcomes[-1]['original_interrupted_record']=interrupted;outcomes[-1]['physical_audit_passed']=True;outcomes[-1]['strict_success']=False
dump(window/'CONFIRMATION_RESULTS.json',outcomes);dump(root/'FINAL_PHYSICAL_AUDITS.json',physical);dump(window/'SELECTION_FREEZE.json',selection);ledger=[];repeats=[]
baseline_tasks=[(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]
def remaining():
    return limit-(time.monotonic()-start)

def frozen():
    assert hashlib.sha256((src/'PROTOCOL.md').read_bytes()).hexdigest() == protocol_hash
    assert all(hashlib.sha256((src/name).read_bytes()).hexdigest() == digest for name,digest in freeze.items()), 'SOURCE_CHANGED'

def execute(cmd, log, seconds):
    with log.open('w') as stream:
        proc = subprocess.Popen(cmd,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            return proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            return 124
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            raise

def run(name, seed, scene, feasibility=False):
    frozen()
    if remaining() < (46 if feasibility else 960):
        return None
    dump(window/'ACTIVE.json',{'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'started_unix':time.time()})
    cmd = [str(repo/'run_phase.sh'),str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(seed),'--scene',scene,'--conditions','geometry_memory','--wall-seconds',str(40 if feasibility else 900),'--max-steps','1200']
    if feasibility: cmd += ['--feasibility-only']
    begin = time.monotonic()
    code = execute(cmd,window/(name+'.console'),45 if feasibility else 905)
    pair = root/name/'paired'
    row = {'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'returncode':code,'wall_s':time.monotonic()-begin,'completion':read(pair/'completion.json'),'preflight':read(pair/'PREFLIGHT.json'),'feasibility':read(pair/'TASK_FEASIBILITY.json'),'protocol':read(pair/'STATIC_PROTOCOL.json'),'interrupted':read(pair/'geometry_memory/interrupted.json'),'run_root':'runs/v653_static_log_recovery'}
    ledger.append(row)
    dump(window/'LEDGER.json',ledger)
    dump(window/'ACTIVE.json',{'status':'IDLE','last_completed':name})
    print(name,'code',code,'eligible',None if row['feasibility'] is None else row['feasibility']['eligible'],'remaining_s',round(remaining(),1),flush=True)
    return row

def audit_run(name, result):
    pair = root/name/'paired'
    if result is None or remaining() < 50: return False
    frozen()
    code = execute([str(repo/'run_phase.sh'),str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'native_replay.console',35)
    replay = read(pair/'NATIVE_REPLAY_AUDIT.json')
    integrity_code = execute(['python',str(repo/'experiments/v648_static_unknown/audit_results.py'),str(pair)],pair/'integrity.console',15)
    cell = pair/'geometry_memory'
    admission = [json.loads(s) for s in (cell/'model_admission.jsonl').read_text().splitlines()]
    plans = {int(f.stem.split('_')[-1]) for f in cell.glob('planning_*.json')}
    transition = cell/'gear_transitions.jsonl'
    switches = {json.loads(s)['step'] for s in transition.read_text().splitlines()} if transition.exists() else set()
    bypasses = [x['step'] for previous,x in zip(admission[:-1],admission[1:]) if x['active_gear'] != previous['active_gear'] and x['step'] not in plans and x['step'] not in switches]
    passed = bool(code == 0 and integrity_code == 0 and replay and replay['status'] == 'MATCHED_RECORDED_PUBLIC_STATES' and replay['maximum_full_public_qpos_error'] <= 1e-8 and replay['maximum_full_public_qvel_error'] <= 1e-8 and replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] >= .15-1e-8 and replay['reconstructed_native_states_below_015'] == 0 and replay['replay_obstacle_contact_records'] == 0 and not bypasses and result['minimum_actual_self_domain_margin_m'] >= 0 and result['self_geometry_checked_native_ticks'] == result['physics_steps'] and result['static_obstacle_pose_unchanged'] and result['root_mutations_outside_mjstep'] == 0 and all(result['contacts'][k] == 0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']))
    physical.append({'name':name,'run_root':'runs/v653_static_log_recovery','passed':passed,'replay':replay,'integrity_passed':integrity_code == 0,'unchecked_cusp_switch_steps':bypasses})
    dump(root/'FINAL_PHYSICAL_AUDITS.json',physical)
    return passed


status='CONTINUATION_RUNNING'
def stop_signal(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP_SIGNAL')
signal.signal(signal.SIGTERM,stop_signal)
try:
 for task in tasks[5:]:
  row=run(f'confirm_{task["seed"]}_{task["scene"]}',task['seed'],task['scene'])
  if row is None:status='CONTINUATION_BUDGET_INCOMPLETE';break
  result=(row['completion']or{}).get('results',[]);result=result[0]if result else None
  same=bool(row['protocol']and row['protocol']['full_model_sha256']==task['scene_model_sha256']);safe=audit_run(row['name'],result);good=bool(result and result['strict_safe_arrival']and same and safe)
  outcomes.append({'name':row['name'],'seed':row['seed'],'scene':row['scene'],'result':result,'strict_success':good,'scene_matches_preflight':same,'physical_audit_passed':safe,'run_root':'runs/v653_static_log_recovery'});dump(window/'CONFIRMATION_RESULTS.json',outcomes)
  print('COMBINED_CONFIRMATION',len(outcomes),'arrivals',sum(x['strict_success']for x in outcomes),'original_interruption_remains_failure',True,flush=True)
  if not safe or not same:status='GATE_FAILED_PHYSICAL_SOURCE_OR_SCENE_AUDIT';break
  if sum(not x['strict_success']for x in outcomes)>=2:status='GATE_FAILED_TWO_NON_SUCCESSES';break
 else:status='NAVIGATION_GATE_PASSED_PENDING_REPEATS'
 if status == 'NAVIGATION_GATE_PASSED_PENDING_REPEATS':
     for seed, scene in baseline_tasks:
         row = run(f'repeat_{seed}_{scene}',seed,scene)
         if row is None: status = 'REPEATS_BUDGET_INCOMPLETE'; break
         result = (row['completion'] or {}).get('results',[])
         result = result[0] if result else None
         safe = audit_run(row['name'],result)
         base = repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
         other = root/row['name']/'paired'
         old_result = read(base/'geometry_memory/result.json')
         old_rows = [json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
         new_log = other/'geometry_memory/v648_execution.jsonl'
         new_rows = [json.loads(s) for s in new_log.read_text().splitlines()] if new_log.exists() else []
         errors = {key:max((float(np.max(np.abs(np.array(a[key])-np.array(b[key])))) for a,b in zip(old_rows,new_rows)),default=float('inf')) for key in ['qpos_full','qvel_full','ctrl']}
         matched = bool(safe and result and result['strict_safe_arrival'] and len(old_rows) == len(new_rows) and max(errors.values()) <= 1e-8 and result['normalized_initial_state_hash'] == old_result['normalized_initial_state_hash'] and result['contacts']['contact_log_content_sha256'] == old_result['contacts']['contact_log_content_sha256'] and read(base/'STATIC_PROTOCOL.json')['full_model_sha256'] == read(other/'STATIC_PROTOCOL.json')['full_model_sha256'])
         repeats.append({'name':row['name'],'seed':seed,'scene':scene,'matched':matched,'full_public_maximum_errors':{k:(v if np.isfinite(v) else None) for k,v in errors.items()},'original_public_steps':len(old_rows),'repeat_public_steps':len(new_rows)})
         dump(window/'REPEAT_AUDIT.json',repeats)
         if not matched: status = 'GATE_FAILED_REPEAT'; break
     else: status = 'ALL_TASKS_AND_REPEATS_AUDITED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 classes={s:sum(x['strict_success']for x in outcomes if x['scene']==s)for s in ['single_event','legacy_two']}
 checks={'same_24_locked_tasks':len(tasks)==24,'all_24_attempt_records':len(outcomes)==24,'at_least_23_strict_arrivals':sum(x['strict_success']for x in outcomes)>=23,'single_at_least_11':classes['single_event']>=11,'two_at_least_11':classes['legacy_two']>=11,'all_27_executed_prefix_or_full_physical_audits':len(physical)==27 and all(x['passed']for x in physical),'three_matching_full_state_repeats':len(repeats)==3 and all(x['matched']for x in repeats),'original_budget_respected':remaining()>=0,'frozen_continuation_source':all(hashlib.sha256((src/n).read_bytes()).hexdigest()==h for n,h in freeze.items()),'decision_equivalence_proved':proof['equivalent'],'original_interruption_not_relabelled':outcomes[4]['strict_success']is False and outcomes[4]['result']is None}
 dump(window/'COMPLETION.json',{'status':status,'elapsed_from_original_origin_s':time.monotonic()-start,'limit_s':limit,'completed_confirmation_attempts':len(outcomes),'strict_arrivals':sum(x['strict_success']for x in outcomes),'class_successes':classes,'original_interrupted_non_successes':1,'remaining_selected_unattempted':tasks[len(outcomes):],'repeats_attempted':len(repeats),'static_engineering_acceptance_passed':all(checks.values()),'checks':checks,'dynamic_started':False,'training_updates':0,'scope':'same locked finite static benchmark and equivalent frozen decisions; original logging interruption is permanently one failure, later runner differs only by proven diagnostic dictionary copies'})
 dump(window/'ACTIVE.json',{'status':status,'completed':True});print('CONTINUATION_COMPLETE',status,'accepted',all(checks.values()),flush=True)
