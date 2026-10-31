"""Bounded sequential host orchestrator; every simulation is Phase-isolated.
Separates all truth-only t0 selections from subsequent frozen navigation outcomes.
"""
import fcntl,hashlib,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];src=Path(__file__).parent;root=repo/'runs/v650_static_acceptance';root.mkdir(exist_ok=True)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=root/'acceptance_window01';previous=json.loads((prior/'COMPLETION.json').read_text());assert previous['status']=='INSUFFICIENT_ELIGIBLE_TASKS'and previous['completed_confirmation_attempts']==0
origin=json.loads((prior/'WINDOW.json').read_text());window=root/'acceptance_window02';window.mkdir();start=time.monotonic()-(time.time()-origin['started_unix']);LIMIT=14400
freeze={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(src.glob('*.py'))}
def dump(p,j):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(j,indent=2,ensure_ascii=False));tmp.replace(p)
dump(window/'SOURCE_FREEZE.json',freeze);dump(window/'WINDOW.json',{'limit_s':LIMIT,'started_unix':time.time(),'started_local':time.strftime('%Y-%m-%d %H:%M:%S %z'),'pid':os.getpid(),'phase_only':True,'dynamic_user_review_required':True})
(src_protocol:=window/'PROTOCOL.md').write_bytes((src/'PROTOCOL.md').read_bytes());(window/'POOL_EXTENSION_PREREG.md').write_bytes((src/'POOL_EXTENSION_PREREG.md').read_bytes())
ledger=json.loads((prior/'LEDGER.json').read_text())
def run(name,seed,scene,feasibility=False):
    for n,h in freeze.items():assert hashlib.sha256((src/n).read_bytes()).hexdigest()==h,'SOURCE_CHANGED_DURING_CONFIRMATION'
    remaining=LIMIT-(time.monotonic()-start)
    if remaining<(40 if feasibility else 905):return None
    cmd=[str(repo/'run_phase.sh'),str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(seed),'--scene',scene,'--conditions','geometry_memory','--wall-seconds',str(40 if feasibility else 900)]
    if feasibility:cmd+=['--feasibility-only']
    begun=time.monotonic();process=None
    with(window/(name+'.console')).open('w')as stream:
        process=subprocess.Popen(cmd,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        dump(window/'ACTIVE.json',{'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'process_group':process.pid,'started_unix':time.time()})
        try:code=process.wait(timeout=45 if feasibility else 905)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            code=124
    paired=root/name/'paired'
    def read(file):
        p=paired/file;return json.loads(p.read_text())if p.exists()else None
    row={'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'returncode':code,'wall_s':time.monotonic()-begun,'completion':read('completion.json'),'preflight':read('PREFLIGHT.json'),'feasibility':read('TASK_FEASIBILITY.json'),'protocol':read('STATIC_PROTOCOL.json')}
    ledger.append(row);dump(window/'LEDGER.json',ledger);dump(window/'ACTIVE.json',{'status':'IDLE','last_completed':name})
    print(json.dumps({'name':name,'code':code,'eligible':None if row['feasibility']is None else row['feasibility']['eligible'],'outcomes':[]if row['completion']is None else[(x['outcome'],x['strict_safe_arrival'])for x in row['completion'].get('results',[])]}),flush=True)
    return row
# No navigation outcomes are consulted while the pool is screened.
for seed in range(93000061,93000181):
    scene='single_event'if seed%2 else'legacy_two'
    if run(f'preflight_{seed}_{scene}',seed,scene,True)is None:break
selected=[]
for scene in ['single_event','legacy_two']:
    candidates=[x for x in ledger if x['scene']==scene and x['feasibility']and x['feasibility']['eligible']]
    selected.extend(candidates[:12])
selected.sort(key=lambda x:x['seed'])
selection={'status':'LOCKED_BEFORE_NAVIGATION','tasks':[{'seed':x['seed'],'scene':x['scene'],'preflight_name':x['name'],'scene_model_sha256':x['protocol']['full_model_sha256']}for x in selected],'counts':{s:sum(x['scene']==s for x in selected)for s in ['single_event','legacy_two']},'screened':len(ledger),'source_freeze_sha256':hashlib.sha256((window/'SOURCE_FREEZE.json').read_bytes()).hexdigest(),'scope':'geometry-reference-selected tasks, not unfiltered random trials'}
dump(window/'SELECTION_FREEZE.json',selection)
outcomes=[];status='INSUFFICIENT_ELIGIBLE_TASKS'
if len(selected)==24:
    status='CONFIRMATION_RUNNING';failures=0
    for task in selected:
        row=run(f'confirm_{task["seed"]}_{task["scene"]}',task['seed'],task['scene'])
        if row is None:status='WINDOW_BUDGET_INCOMPLETE';break
        result=(row['completion']or{}).get('results',[]);result=result[0]if result else None
        scene_same=bool(row['protocol']and row['protocol']['full_model_sha256']==task['protocol']['full_model_sha256'])
        good=bool(result and result['strict_safe_arrival']and scene_same)
        contact=bool(result and any(result['contacts'][k]for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']))
        outcomes.append({'seed':row['seed'],'scene':row['scene'],'name':row['name'],'strict_success':good,'scene_matches_preflight':scene_same,'result':result});failures+=not good
        dump(window/'CONFIRMATION_RESULTS.json',outcomes)
        if contact:status='GATE_FAILED_CONTACT';break
        if failures>=2:status='GATE_FAILED_TWO_NON_SUCCESSES';break
    else:status='NAVIGATION_GATE_PASSED_PENDING_REPEATS_AND_AUDITS'
# Repeats are allowed only after the new-scene navigation gate.
repeats=[]
if status=='NAVIGATION_GATE_PASSED_PENDING_REPEATS_AND_AUDITS':
    for seed,scene in [(91000002,'single_event'),(92000003,'single_event'),(92000005,'legacy_two')]:
        row=run(f'repeat_{seed}_{scene}',seed,scene)
        if row is None:status='REPEATS_BUDGET_INCOMPLETE';break
        repeats.append({'name':row['name'],'seed':seed,'scene':scene,'completion':row['completion']})
    dump(window/'REPEAT_RESULTS.json',repeats)
dump(window/'COMPLETION.json',{'status':status,'elapsed_s':time.monotonic()-start,'window_limit_s':LIMIT,'selected_tasks':len(selected),'completed_confirmation_attempts':len(outcomes),'strict_arrivals':sum(x['strict_success']for x in outcomes),'confirmation_failures':sum(not x['strict_success']for x in outcomes),'repeats_attempted':len(repeats),'remaining_selected_unattempted':[{'seed':x['seed'],'scene':x['scene']}for x in selected[len(outcomes):]],'static_acceptance_passed':False,'reason':'final native clearance, contacts, source/state/repeat audits must be performed; no automatic acceptance','dynamic_started':False,'training_updates':0})
print('WINDOW_COMPLETE',status,flush=True)
