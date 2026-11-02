"""One immutable fresh24 confirmation; no tuning or automatic new batch."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path

repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent
worker=repo/'experiments/v697_rpccr_dynamic_initialization'
root=repo/'runs/v698_rpccr_dynamic_confirmation';worker_root=repo/'runs/v697_rpccr_dynamic_initialization'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(path)

freeze=read(own/'CANDIDATE_FREEZE.json')
candidate_sha=sha(own/'CANDIDATE_FREEZE.json')
def unchanged():
    assert sha(own/'CANDIDATE_FREEZE.json')==candidate_sha,'CANDIDATE_FREEZE_CHANGED'
    assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_SOURCE_MODEL_OR_OLD_EVIDENCE_CHANGED'
unchanged()
assert read(repo/'runs/v697_rpccr_dynamic_initialization/FINAL_EVIDENCE_ACCOUNT.json')['status']=='ALL_FINAL_EVIDENCE_CHECKS_PASS','PREREQUISITE_NOT_PASSED'
root.mkdir(exist_ok=True);lock=(root/'window.lock').open('a+')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
phase_lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+')
fcntl.flock(phase_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(phase_lock,fcntl.LOCK_UN)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=root/'confirmation01';window.mkdir();started=time.time();deadline=started+15000
tasks=read(own/'TASK_LIST.json');assert len(tasks)==len({t['seed'] for t in tasks})==24
for task in tasks:
    for name in ['v698_t0_slot%02d'%task['slot'],'v698_slot%02d'%task['slot']]:
        assert not (worker_root/name).exists(),'REGISTERED_TASK_OUTPUT_ALREADY_EXISTS'
dump(window/'LOCKED_TASK_LIST.json',tasks)
dump(window/'SOURCE_FREEZE.json',{p.name:sha(p) for p in worker.glob('*.py')})
dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p) for p in worker.glob('*.md')})
dump(window/'CONFIRMATION_SOURCE_FREEZE.json',{str(p.relative_to(repo)):sha(p) for p in own.glob('*') if p.suffix in ['.py','.md','.json']})
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'
external=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py'
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':15000,'pid':os.getpid(),'round_closed':False,'preflight_attempts':0,'navigation_attempts':0,'confirmation_main_attempts':0,'confirmation_repeat_attempts':0,'algorithm_revisions':0,'gradient_updates':0,'sac_gradient_updates':0,'single_cpu_sequential':True,'static_experiments':0,'stage_access':0,'real_robot':0,'fresh_confirmation_gate_passed':False}
dump(root/'ROUND_WINDOW.json',ledger)
results=[];preflights=[];status='RUNNING';non_successes=0
def execute(args,log,cap,envvars=None):
    unchanged();assert time.time()+cap+3<deadline,'INSUFFICIENT_REMAINING_ABSOLUTE_WINDOW'
    dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time(),'child_cap_s':cap,'absolute_batch_deadline_unix':deadline,'env':envvars})
    env=os.environ.copy();env.update(envvars or {})
    with log.open('w') as stream:
        child=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:return child.wait(timeout=min(cap,max(.1,deadline-time.time())))
        except BaseException:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise

def run(task,preflight=False,repeat=False):
    slot=task['slot'];name=('v698_t0_slot%02d' if preflight else 'v698_repeat_slot%02d' if repeat else 'v698_slot%02d')%slot
    ledger['preflight_attempts' if preflight else 'navigation_attempts']+=1
    if not preflight:ledger['confirmation_repeat_attempts' if repeat else 'confirmation_main_attempts']+=1
    assert ledger['preflight_attempts']<=24 and ledger['confirmation_main_attempts']<=24 and ledger['confirmation_repeat_attempts']<=3
    dump(root/'ROUND_WINDOW.json',ledger)
    pair=worker_root/name/'paired'
    if not preflight:
        results.append({'name':name,'task':task,'repeat':repeat,'run':str(pair.relative_to(repo)),'runner_exit':None,'result':None,'functional_passed':False,'physical_audits_passed':False});dump(window/'RESULTS.json',results)
    env={'PHASE_COURSE_DISTANCE':'8','PHASE_COURSE_PHASE':str(task['phase']),'PHASE_PROPOSAL_MODEL':str(model)}
    args=[str(worker.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(task['seed']),'--wall-seconds',str(45 if preflight else 900),'--max-steps','1200','--initial-observation-steps','0']
    if preflight:args+=['--feasibility-only']
    code=execute(args,window/(name+'.console'),50 if preflight else 905,env)
    if preflight:
        record={'task':task,'run':str(pair.relative_to(repo)),'runner_exit':code};preflights.append(record);dump(window/'PREFLIGHTS.json',preflights)
        assert code==0,'PREFLIGHT_RUNNER_FAILED'
        assert execute([str(worker.relative_to(repo)/'audit_discovery.py'),str(pair),'--preflight'],pair/'initial_unseen_audit.console',30)==0,'PREFLIGHT_CAUSAL_AUDIT_FAILED'
        assert read(pair/'TASK_FEASIBILITY.json')['eligible'],'PREFLIGHT_REFERENCE_FAILED'
        return pair
    record=results[-1];record['runner_exit']=code
    completion=read(pair/'completion.json') if (pair/'completion.json').exists() else None
    record['completion']=completion
    result_path=pair/'geometry_memory/result.json';partial_path=pair/'geometry_memory/interrupted.json'
    r=read(result_path) if result_path.exists() else None;partial=read(partial_path) if partial_path.exists() else None
    record.update(result=r,interrupted=partial);dump(window/'RESULTS.json',results)
    if r is not None or (partial and partial['public_steps']>0):
        assert execute([str(worker.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'replay.console',35)==0,'REPLAY_EXECUTION_FAILED'
        assert read(pair/'NATIVE_REPLAY_AUDIT.json')['status']=='MATCHED_RECORDED_PUBLIC_STATES','REPLAY_MISMATCH'
    assert code==0 and r is not None,'TASK_RUNNER_OR_EVIDENCE_EXCEPTION'
    for script,log,cap in [('audit_run.py','physical_audit',55),('audit_route_commitment.py','route_audit',60),('audit_projection_learning.py','projection_learning',60)]:
        args=[str(worker.relative_to(repo)/script),str(pair)]
        if script=='audit_run.py':args+=['--window',str(window)]
        if script=='audit_projection_learning.py':args+=['--model',str(model)]
        assert execute(args,pair/(log+'.console'),cap)==0,script+'_FAILED'
    dump(pair/'TAIL_AUDITOR_SOURCE.json',{'path':str(external.relative_to(repo)),'sha256':sha(external)})
    assert execute([str(external.relative_to(repo)),str(pair)],pair/'tail_audit.console',40)==0,'TAIL_AUDIT_FAILED'
    chain_code=execute([str(worker.relative_to(repo)/'audit_discovery.py'),str(pair)],pair/'discovery_chain.console',60)
    chain_path=pair/'DISCOVERY_CHAIN_AUDIT.json';assert chain_path.exists(),'CHAIN_AUDITOR_EXCEPTION'
    chain=read(chain_path);functional_keys={'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'}
    failed={k for k,v in chain['checks'].items() if not v};assert not (failed-functional_keys),'CAUSAL_STATE_SAFETY_OR_STOP_CHAIN_ANOMALY:'+str(sorted(failed-functional_keys))
    assert chain_code in (0,1),'CHAIN_PROCESS_ANOMALY'
    assert (chain_code==0)==(chain['status']=='PASS' and not failed),'CHAIN_STATUS_EXIT_MISMATCH'
    record.update(physical_audits_passed=True,discovery_chain_audit_passed=chain_code==0,functional_passed=bool(r['strict_safe_arrival'] and chain['status']=='PASS' and all(chain['checks'].values())),functional_failed_checks=sorted(failed));dump(window/'RESULTS.json',results)
    return pair

def repeat_compare(base,pair):
    import numpy as np
    sys.path.insert(0,str(worker));from contact_fingerprint import compare_contacts
    a=[json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];b=[json.loads(s) for s in (pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={k:float(np.max(abs(np.asarray([x[k] for x in a])-np.asarray([x[k] for x in b])))) if len(a)==len(b) else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
    contacts=compare_contacts(base,pair);checks={'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'same_initial':read(base/'geometry_memory/result.json')['normalized_initial_state_hash']==read(pair/'geometry_memory/result.json')['normalized_initial_state_hash'],'full_state_ctrl_error':all(v is not None and v<=1e-8 for v in errors.values()),'all_real_contacts':contacts['passed'],'same_discovery_event':read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json')}
    dump(pair/'EXACT_REPEAT_AUDIT.json',{'passed':all(checks.values()),'checks':checks,'errors':errors,'contacts':contacts});assert all(checks.values()),'COMPLETE_REPEAT_FAILED'

try:
    for task in tasks:run(task,preflight=True)
    assert execute([str(own.relative_to(repo)/'audit_preflight.py')],window/'preflight_independent.console',30)==0,'INDEPENDENT_PREFLIGHT_OR_NOISE_AUDIT_FAILED'
    baselines={}
    for task in tasks:
        baselines[task['slot']]=run(task)
        if not results[-1]['functional_passed']:non_successes+=1
        assert non_successes<2,'SECOND_FUNCTIONAL_NON_SUCCESS'
    groups={g:sum(x['functional_passed'] for x in results if x['task']['initial_motion_direction']==g) for g in ['POSITIVE_Y','NEGATIVE_Y']}
    assert len(results)==24 and sum(groups.values())>=23 and min(groups.values())>=11,'FIXED24_FUNCTIONAL_GATE_FAILED'
    for slot in [1,8,20]:
        assert results[slot-1]['functional_passed'],'PRESELECTED_REPEAT_BASELINE_NOT_SUCCESSFUL'
        again=run(tasks[slot-1],repeat=True);assert results[-1]['functional_passed'],'REPEAT_FUNCTIONAL_NON_SUCCESS'
        repeat_compare(baselines[slot],again)
    unchanged();ledger['fresh_confirmation_gate_passed']=True;status='PROVISIONAL_FRESH24_AND_THREE_REPEATS_PASS'
except BaseException as e:
    status='STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
    ledger.update(status=status,round_closed=True,elapsed_s=time.time()-started,non_successes=non_successes);dump(root/'ROUND_WINDOW.json',ledger)
    dump(window/'COMPLETION.json',{'status':status,'round_closed':True,'results':results,'preflights':preflights,'fresh_confirmation_gate_passed':ledger['fresh_confirmation_gate_passed'],'elapsed_s':ledger['elapsed_s'],'automatic_additional_simulation':False})
    dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
    # Deterministic zero-simulation closure does not start or renew any task.
    with (root/'finalize.console').open('w') as stream:
        child=subprocess.Popen([sys.executable,'-B',str(own/'finalize.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:child.wait(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
