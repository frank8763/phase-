"""Bounded initialization-only engineering revision and two exact old anchors."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path

repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent
root=repo/'runs/v704_bootstrap_repair';auditor=repo/'experiments/v699_dynamic_packet_audit'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');temp.replace(p)
freeze=read(own/'CANDIDATE_FREEZE.json');freeze_sha=sha(own/'CANDIDATE_FREEZE.json')
def unchanged():
    assert sha(own/'CANDIDATE_FREEZE.json')==freeze_sha
    assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
unchanged();assert read(repo/'runs/v700_rpccr_dynamic_continuation/FINALIZED.json')['status']=='FINITE_MOVING_DISCOVERY_SAME24_CONTINUATION_PASS'
root.mkdir(exist_ok=True);lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
window=root/'repair01';window.mkdir();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
started=time.time();deadline=started+2700
plan=read(own/'EXECUTION_PLAN.json');tasks={x['slot']:x for x in read(own/'TASK_LIST.json')};tasks[0]=read(own/'ANCHOR_TASK.json')
for item in plan:assert not (root/item['name']).exists(),'OUTPUT_ALREADY_EXISTS'
dump(window/'LOCKED_TASK_LIST.json',list(tasks.values()));dump(window/'LOCKED_EXECUTION_PLAN.json',plan)
dump(window/'SOURCE_FREEZE.json',{p.name:sha(p) for p in own.glob('*.py')})
dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p) for p in own.glob('*.md')})
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':2700,'pid':os.getpid(),'round_closed':False,'navigation_attempts':0,'max_navigation_executions':2,'training_updates':0,'algorithm_revisions':0,'stage_access':0,'real_robot':0,'single_cpu_sequential':True}
dump(root/'ROUND_WINDOW.json',ledger);results=[];status='RUNNING';model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'
def execute(args,log,cap,envvars=None):
    unchanged();assert time.time()+cap+3<deadline,'INSUFFICIENT_ABSOLUTE_BUDGET'
    dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time(),'child_cap_s':cap,'absolute_deadline_unix':deadline,'env':envvars})
    env=os.environ.copy();env.update(envvars or {})
    with log.open('w') as stream:
        process=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:return process.wait(timeout=min(cap,deadline-time.time()))
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            raise
def compare(base,pair,require_arrival):
    import numpy as np
    sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
    aa=[json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    bb=[json.loads(s) for s in (pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
    errors={k:float(np.max(abs(np.asarray([x[k] for x in aa])-np.asarray([x[k] for x in bb])))) if len(aa)==len(bb) and aa else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
    a=read(base/'geometry_memory/result.json');b=read(pair/'geometry_memory/result.json');contacts=compare_contacts(base,pair)
    checks={'full_state_ctrl':all(v is not None and v<=1e-8 for v in errors.values()),'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'same_normalized_initial':a['normalized_initial_state_hash']==b['normalized_initial_state_hash'],'same_outcome':a['outcome']==b['outcome'] and a['strict_safe_arrival']==b['strict_safe_arrival'],'real_contact_events':contacts['passed'],'same_discovery':read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json'),'required_arrival':not require_arrival or b['strict_safe_arrival']}
    out={'passed':all(checks.values()),'checks':checks,'errors':errors,'contacts':contacts,'base':str(base.relative_to(repo)),'new_navigation_samples':0}
    dump(pair/'EXACT_COMPARISON_AUDIT.json',out);assert out['passed'],'EXACT_REFERENCE_OR_REPEAT_MISMATCH'
try:
    preflights=[]
    for task in read(own/'TASK_LIST.json'):
        name='t0_slot%02d'%task['slot'];pair=root/name/'paired'
        env={'PHASE_RECOVERY_ABLATION':'FULL','PHASE_COURSE_DISTANCE':'8','PHASE_COURSE_PHASE':str(task['phase']),'PHASE_PROPOSAL_MODEL':str(model)}
        code=execute([str(own.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(task['seed']),'--wall-seconds','45','--max-steps','1200','--initial-observation-steps','0','--feasibility-only'],window/(name+'.console'),50,env)
        assert code==0,'NEW_PREFLIGHT_FAILED'
        assert execute([str(auditor.relative_to(repo)/'audit_discovery.py'),str(pair),'--preflight','--output-dir',str(pair/'v699_preflight')],window/(name+'_audit.console'),30)==0,'NEW_PREFLIGHT_CAUSAL_FAILED'
        preflights.append({'task':task,'run':str(pair.relative_to(repo)),'runner_exit':code});dump(window/'PREFLIGHTS.json',preflights)
    assert execute([str(own.relative_to(repo)/'audit_preflight.py')],window/'preflight_noise.console',30)==0,'NEW_PREFLIGHT_NOISE_AUDIT_FAILED'
    for item in plan:
        task=tasks[item['slot']];pair=root/item['name']/'paired';record={**item,'task':task,'run':str(pair.relative_to(repo)),'runner_exit':None,'functional_passed':False,'physical_passed':False}
        if item['role']=='FULL_REPEAT':assert next(x for x in results if x['name']==item['repeat_of'])['physical_passed'],'REPEAT_PREREQUISITE_FAILED'
        ledger['navigation_attempts']+=1;assert ledger['navigation_attempts']<=2;dump(root/'ROUND_WINDOW.json',ledger)
        results.append(record);dump(window/'RESULTS.json',results)
        env={'PHASE_RECOVERY_ABLATION':item['mode'],'PHASE_COURSE_DISTANCE':'8','PHASE_COURSE_PHASE':str(task['phase']),'PHASE_PROPOSAL_MODEL':str(model)}
        args=[str(own.relative_to(repo)/'run_static.py'),'--name',item['name'],'--seed',str(task['seed']),'--wall-seconds','900','--max-steps','1200','--initial-observation-steps','0']
        code=execute(args,window/(item['name']+'.console'),905,env);record['runner_exit']=code
        observed=pair/'geometry_memory/result.json';record['result']=read(observed) if observed.exists() else None
        partial=pair/'geometry_memory/interrupted.json';record['interrupted']=read(partial) if partial.exists() else None;dump(window/'RESULTS.json',results)
        if record['result'] is not None or (record['interrupted'] or {}).get('public_steps',0)>0:
            assert execute([str(own.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'replay.console',35)==0,'REPLAY_EXCEPTION'
        assert code==0 and record['result'] is not None,'INCOMPLETE_TASK_EVIDENCE_STOP'
        for script,cap in [('audit_run.py',55),('audit_route_commitment.py',60),('audit_projection_learning.py',60)]:
            args=[str(own.relative_to(repo)/script),str(pair)]
            if script=='audit_run.py':args+=['--window',str(window)]
            if script=='audit_projection_learning.py':args+=['--model',str(model)]
            assert execute(args,pair/(script+'.console'),cap)==0,script+'_FAILED'
        external=own/'audit_all_tail_geometry.py'
        dump(pair/'TAIL_AUDITOR_SOURCE.json',{'path':str(external.relative_to(repo)),'sha256':sha(external)})
        assert execute([str(external.relative_to(repo)),str(pair)],pair/'tail_audit.console',40)==0,'TAIL_AUDIT_FAILED'
        output=pair/'v699_discovery_audit';chain_code=execute([str(auditor.relative_to(repo)/'audit_discovery.py'),str(pair),'--output-dir',str(output)],pair/'discovery_audit.console',60)
        chain_path=output/'DISCOVERY_CHAIN_AUDIT_V699.json';assert chain_path.exists(),'CHAIN_AUDIT_CRASH'
        chain=read(chain_path);failed=[k for k,v in chain['checks'].items() if not v]
        assert not(set(failed)-{'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'}),'NONFUNCTIONAL_CHAIN_EXCEPTION'
        assert chain_code in (0,1) and (chain_code==0)==(chain['status']=='PASS' and not failed),'CHAIN_EXIT_INCONSISTENT'
        assert execute([str(own.relative_to(repo)/'audit_shadow_mode.py'),str(pair)],pair/'mechanism_audit.console',30)==0,'MECHANISM_CONTRACT_FAILED'
        record.update(physical_passed=True,functional_passed=bool(record['result']['strict_safe_arrival'] and chain['status']=='PASS'),functional_failed_checks=failed);dump(window/'RESULTS.json',results)
        if item['role']=='ANCHOR_REFERENCE':
            assert record['functional_passed'],'ANCHOR_REFERENCE_NOT_ARRIVED'
            compare(repo/'runs/v701_rpccr_recovery_ablation/full14/paired',pair,True)
        elif item['role']=='ANCHOR_SHADOW':
            compare(repo/'runs/v701_rpccr_recovery_ablation/tail14/paired',pair,False)
            assert execute([str(own.relative_to(repo)/'audit_pair.py'),str(root/'anchor_full/paired'),str(pair),'--output',str(window/'ANCHOR_PAIR_AUDIT.json')],window/'anchor_pair.console',35)==0,'ANCHOR_COMPUTE_OR_PREFIX_MISMATCH'
            assert read(window/'ANCHOR_PAIR_AUDIT.json')['mechanism_triggered'],'ANCHOR_NOT_TRIGGERED'
        elif item['role']=='FULL_REPEAT':compare(root/item['repeat_of']/'paired',pair,False)
        elif item['role']=='PROSPECTIVE_MAIN':
            done={x['name'] for x in results if x.get('physical_passed')};n=item['slot']
            if 'full%d'%n in done and 'shadow%d'%n in done:
                assert execute([str(own.relative_to(repo)/'audit_pair.py'),str(root/('full%d'%n)/'paired'),str(root/('shadow%d'%n)/'paired'),'--output',str(window/('PAIR_%02d.json'%n))],window/('pair%02d.console'%n),35)==0,'NEW_PAIR_COMPUTE_OR_PREFIX_MISMATCH'
    unchanged();status='BOOTSTRAP_REPAIR_ANCHORS_COMPLETE'
except BaseException as error:
    status='STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
    ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger)
    dump(window/'COMPLETION.json',{'status':status,'round_closed':True,'results':results,'automatic_additional_simulation':False})
    dump(window/'ACTIVE.json',{'status':status,'completed':True})
    with (root/'finalize.console').open('w') as stream:
        process=subprocess.Popen([sys.executable,'-B',str(own/'finalize_repair.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
