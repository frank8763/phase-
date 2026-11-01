"""One finite explicit 6m then conditional 8m training window."""
import os,sys,time,signal,subprocess,json,hashlib,fcntl,traceback,math
from pathlib import Path
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v689_dynamic_route_commitment';root.mkdir(exist_ok=True)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=root/'curriculum01';window.mkdir();started=time.time();deadline=started+7200
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={p.name:sha(p)for p in src.glob('*.py')};documents={p.name:sha(p)for p in src.glob('*.md')};dump(window/'SOURCE_FREEZE.json',sources);dump(window/'DOCUMENT_FREEZE.json',documents)
external=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py';external_sha=sha(external);dump(window/'EXTERNAL_AUDITOR_FREEZE.json',{'path':str(external.relative_to(repo)),'sha256':external_sha})
dump(window/'INITIAL_LEARNER_FREEZE.json',{'path':'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json','sha256':'c77b5f833fe77d3cadbab9fb41835426a058249728eee94a0cf8e92aa88796c0'})
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':7200,'round_closed':False,'pid':os.getpid(),'navigation_attempts':0,'preflight_attempts':0,'supervised_gradient_updates':0,'sac_gradient_updates':0,'six_meter_gate_passed':False,'eight_meter_started':False,'stage_access':0,'single_cpu_sequential':True};dump(root/'ROUND_WINDOW.json',ledger)
results=[];training=[];status='RUNNING'
def execute(args,log,cap,envvars=None):
    assert time.time()+cap+3<deadline,'INSUFFICIENT_REMAINING_WINDOW'
    assert all(sha(src/n)==h for n,h in {**sources,**documents}.items())and sha(external)==external_sha,'FROZEN_SOURCE_CHANGED'
    dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time(),'env':envvars})
    env=os.environ.copy();env.update(envvars or {})
    with log.open('w')as f:
        child=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:return child.wait(timeout=cap)
        except BaseException:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
def run(distance,phase,name,model=None,preflight=False):
    if preflight:ledger['preflight_attempts']+=1
    else:ledger['navigation_attempts']+=1
    assert ledger['navigation_attempts']<=6;dump(root/'ROUND_WINDOW.json',ledger)
    env={'PHASE_COURSE_DISTANCE':str(distance),'PHASE_COURSE_PHASE':str(phase)}
    if model:env['PHASE_PROPOSAL_MODEL']=str(model)
    command=[str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed','95000011','--wall-seconds',str(45 if preflight else 900),'--max-steps',str(900 if distance==6 else 1100),'--initial-observation-steps','32']
    if preflight:command+=['--feasibility-only']
    code=execute(command,window/(name+'.console'),50 if preflight else 905,env);pair=root/name/'paired'
    if not preflight:
        completion=read(pair/'completion.json');results.append({'name':name,'distance_m':distance,'phase':phase,'model':None if model is None else str(model.relative_to(repo)),'result':next(iter(completion.get('results',[])),None),'runner_exit':code,'run':str(pair.relative_to(repo))});dump(window/'RESULTS.json',results)
    assert code==0,'TASK_RUNNER_FAILED'
    if preflight:
        assert read(pair/'TASK_FEASIBILITY.json')['eligible'];return pair
    assert execute([str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'replay.console',35)==0
    assert execute([str(src.relative_to(repo)/'audit_run.py'),str(pair),'--window',str(window)],pair/'audit.console',50)==0,'PHYSICAL_AUDIT_FAILURE'
    assert execute([str(src.relative_to(repo)/'audit_route_commitment.py'),str(pair)],pair/'route_commitment.console',60)==0,'ROUTE_COMMITMENT_AUDIT_FAILURE'
    args=[str(src.relative_to(repo)/'audit_projection_learning.py'),str(pair)]
    if model:args+=['--model',str(model)]
    assert execute(args,pair/'projection_learning.console',60)==0,'CAUSAL_OR_LEARNING_AUDIT_FAILURE'
    helper=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py';dump(pair/'TAIL_AUDITOR_SOURCE.json',{'path':str(helper.relative_to(repo)),'sha256':sha(helper)})
    assert execute([str(helper.relative_to(repo)),str(pair)],pair/'tail_audit.console',40)==0,'TAIL_AUDIT_FAILURE'
    results[-1]['evidence_audits_pass']=True;dump(window/'RESULTS.json',results)
    if not results[-1]['result']['strict_safe_arrival']:raise RuntimeError('CLOSED_NON_ARRIVAL_'+name)
    if model:assert read(pair/'PROJECTION_LEARNING_AUDIT.json')['learned_actual_ordinary_steps']>0,'LEARNED_PROPOSER_NEVER_EXECUTED'
    return pair
def train(pair,distance,initial=None):
    out=root/('training_'+str(distance)+'m');args=[str(src.relative_to(repo)/'train_proposer.py'),'--teacher',str(pair),'--output',str(out)]
    if initial:args+=['--initial',str(initial)]
    assert execute(args,window/('training_'+str(distance)+'m.console'),65)==0,'TRAINING_FAILED'
    report=read(out/'TRAINING.json');assert report['gradient_updates']==512
    training.append(report);ledger['supervised_gradient_updates']+=512;dump(root/'ROUND_WINDOW.json',ledger);dump(window/'TRAINING.json',training)
    return out/'proposer.json'
def repeat(base,pair):
    import numpy as np
    from contact_fingerprint import compare_contacts
    a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={k:float(np.max(abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))if len(a)==len(b)else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
    contacts=compare_contacts(base,pair);aa=read(base/'geometry_memory/result.json');bb=read(pair/'geometry_memory/result.json')
    checks={'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'same_initial':aa['normalized_initial_state_hash']==bb['normalized_initial_state_hash'],'exact_full_state_ctrl':all(v is not None and v<=1e-8 for v in errors.values()),'contacts':contacts['passed']}
    dump(pair/'EXACT_REPEAT_AUDIT.json',{'checks':checks,'errors':errors,'contacts':contacts,'passed':all(checks.values())});assert all(checks.values()),'COMPLETE_REPEAT_FAILED'
try:
    assert read(root/'PRE_NAV_POLICY_VALIDATION.json')['status']=='PASS'
    model6=repo/'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json'
    assert sha(model6)=='c77b5f833fe77d3cadbab9fb41835426a058249728eee94a0cf8e92aa88796c0'
    run(6,0.,'learned6m_train_task',model6)
    test=run(6,math.pi/2,'learned6m_phase_holdout',model6)
    again=run(6,math.pi/2,'learned6m_phase_holdout_repeat',model6);repeat(test,again)
    ledger['six_meter_gate_passed']=True;ledger['eight_meter_started']=True;dump(root/'ROUND_WINDOW.json',ledger)
    run(8,0.,'preflight8m',preflight=True)
    teacher8=run(8,0.,'teacher8m');model8=train(teacher8,8,model6)
    test8=run(8,math.pi/2,'learned8m_phase_holdout',model8)
    again8=run(8,math.pi/2,'learned8m_phase_holdout_repeat',model8);repeat(test8,again8)
    status='SIX_AND_EIGHT_METER_FINITE_CURRICULUM_PASS'
except BaseException as e:
    status='CLOSED_DEPENDENCY_NON_ARRIVAL'if str(e).startswith('CLOSED_NON_ARRIVAL')else'STOPPED_EXCEPTION'
    dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
    ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger)
    dump(window/'COMPLETION.json',{'status':status,'results':results,'training':training,'round_closed':True,'elapsed_s':time.time()-started,'six_meter_gate_passed':ledger['six_meter_gate_passed'],'eight_meter_started':ledger['eight_meter_started'],'automatic_additional_simulation':False,'no_independent_dynamic_stability_claim':True})
    dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
