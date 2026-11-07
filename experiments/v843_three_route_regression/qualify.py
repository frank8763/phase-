"""Real saved auditor interfaces, task registration, control mutations and OS guards; no models."""
import ast,copy,fcntl,importlib.abc,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from common import *
from registration import transform,prefix_anchor,ANCHORS
Q=ROOT/'qualification';Q.mkdir(exist_ok=False);guard=(R/'REVIEW_PENDING').read_bytes();(Q/'REVIEW_PENDING.before').write_bytes(guard);lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});rows=[];passed=False;child=None
def view(base,name,mutate=False):
 pair=Q/name/'paired';pair.mkdir(parents=True);(pair.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True);outputs={file for _,file,_ in AUDITS}|{'discovery_audit','EXACT_REPEAT_AUDIT.json','FINAL_INDEPENDENT_REPEAT.json'}
 for p in base.iterdir():
  if p.name not in outputs and p.name!='geometry_memory'and not p.name.endswith('.console')and not p.name.endswith('.execution.json'):(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
 cell=pair/'geometry_memory';cell.mkdir()
 for p in(base/'geometry_memory').iterdir():
  if mutate and p.name=='v648_execution.jsonl':
   records=[json.loads(s)for s in p.open()];ids=read(base/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json')['ids'];records[0]['ctrl'][ids[-1]]+=.05;(cell/p.name).write_text(''.join(json.dumps(x)+'\n'for x in records))
  else:(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
 return pair
def run(script,args,label,cap=1200,proxy=False,write_root=None):
 global child
 target=Path(write_root or args[0]);command=[str(R/'run_phase.sh'),str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(target)]
 if proxy:command+=['--metadata-proxy']
 command+=[script,*map(str,args)]
 with(Q/(label+'.console')).open('x')as out:
  child=subprocess.Popen(command,cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=cap)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   child=None
try:
 old=read(R/'experiments/staged_audit_completion_20261106/DEVELOPMENT_FREEZE.json');assert all(sha(R/p)==h for p,h in old['files'].items())
 dep=read(R/'runs/v842_staged_long_navigation/development12/FINALIZED.json');assert all(dep[k]for k in ['development_passed','independent_audit_passed','complete_chain_passed','native_replay_exact','source_unchanged','source_and_decompressed_sha_verified'])
 expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses'];base=RAW/'long_main08/paired';pair=view(base,'actual_v842_goal')
 for script,_,_ in AUDITS:transform(script,(W/script).read_text())
 (R/'REVIEW_PENDING').unlink()
 for script,filename,cap in AUDITS:
  args=[pair]
  if script=='audit_run.py':args+=['--window',RAW/'development12']
  if script=='audit_projection_learning.py':args+=['--model',R/'runs/v690_visible_eight_meter/training_8m/proposer.json']
  started=time.time();code=run(script,args,script,cap,proxy=script=='audit_run.py');rows.append(dict(script=script,exit=code,elapsed_s=time.time()-started));dump(Q/'RESULTS.json',rows);assert code==0,script+'_ACTUAL_SAVED_INTERFACE_FAILED';data=read(pair/filename);assert data['status']==expected[script]and all(data.get('checks',{}).values())
 # All three real saved t0 entries, unchanged task dictionaries and exact raw noise.
 phase=Q/'three_t0';phase.mkdir();pre=read(R/'runs/v827_goal_route_validation/development01/PREFLIGHTS.json');assert[x['task']for x in pre]==tasks();dump(phase/'PREFLIGHTS.json',pre);dump(phase/'LOCKED_T0_TASK_LIST.json',tasks());assert run('audit_field_preflight.py',[phase],'registered_three_t0',60)==0
 negatives=0
 for label,records,locked in [('missing_task',pre[:-1],tasks()),('wrong_phase',[dict(x,task=dict(x['task'],phase=x['task']['phase']+.01))if i==0 else x for i,x in enumerate(pre)],tasks())]:
  dest=Q/label;dest.mkdir();dump(dest/'PREFLIGHTS.json',records);dump(dest/'LOCKED_T0_TASK_LIST.json',locked);assert run('audit_field_preflight.py',[dest],label,60)!=0;negatives+=1
 # Route-specific real raw packets/discovery and correct per-route prefix selection.
 anchors={10010002:'repeat_slot02',10010001:'main_slot01',10010003:'main_slot03'};route_results=[]
 for task in tasks():
  actual=R/'runs/v827_goal_route_validation'/anchors[task['seed']]/'paired';v=view(actual,'route_'+str(task['seed']));assert prefix_anchor(task['seed'])==actual/'geometry_memory';assert run('audit_field_discovery.py',[v,'--output-dir',v/'discovery_audit'],'route_discovery_'+str(task['seed']),300)==0;chain=read(v/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');assert chain['status']=='PASS'and all(chain['checks'].values());route_results.append(dict(seed=task['seed'],raw_packet_chain_interface=True,prefix_anchor=str(prefix_anchor(task['seed']).relative_to(R)),is_new_V842_navigation=False))
 try:prefix_anchor(99999999)
 except AssertionError:negatives+=1
 else:raise AssertionError('UNREGISTERED_PREFIX_NOT_REJECTED')
 mutated=view(base,'tampered_control',True);assert run('audit_run.py',[mutated,'--window',RAW/'development12'],'tampered_control',600,True)!=0;bad=read(mutated/'INDEPENDENT_CANONICAL_AUDIT.json');assert bad['status']=='FAIL'and not bad['checks']['raw_admission_ctrl'];negatives+=1
 # Stage gate tests are synthetic and never counted as navigation evidence.
 synthetic=[dict(task=t,role=role,physical_passed=True,functional_passed=True,repeat_passed=role=='REPEAT')for t in tasks()for role in ['MAIN','REPEAT']];assert complete_gate(synthetic)
 for bad in [synthetic[:-1],list(reversed(synthetic)),[dict(x,functional_passed=False)if i==0 else x for i,x in enumerate(synthetic)],[dict(x,repeat_passed=False)if i==1 else x for i,x in enumerate(synthetic)]]:assert not complete_gate(bad);negatives+=1
 assert model_fits(1000,0,720)and not model_fits(100,99,2)
 os_cases=[]
 for label,entry,deadline,expected_ok in [('correct',str(Path(__file__).resolve()),time.time()+60,True),('wrong',str(R/'experiments/staged_90_then12_20261106/campaign.py'),time.time()+60,False),('expired',str(Path(__file__).resolve()),time.time()-1,False)]:
  p=subprocess.run([sys.executable,'-B',str(C/'os_watch.py'),'--probe-only','--pid',str(os.getpid()),'--entrypoint',entry,'--deadline',str(deadline)],capture_output=True,text=True,timeout=5);(Q/('os_'+label+'.console')).write_text(p.stdout+p.stderr);assert(p.returncode==0)==expected_ok;os_cases.append(dict(case=label,expected=expected_ok,exit=p.returncode))
 passed=True;dump(ROOT/'QUALIFICATION.json',dict(passed=True,actual_saved17_auditors=rows,expected_audit_statuses=expected,three_real_t0_interface_passed=True,route_raw_discovery_interfaces=route_results,negative_cases=negatives,prior_complete9601_witness10_mutation_negatives=read(R/'runs/staged_audit_completion_20261106/COMPLETE_COVERAGE_NEGATIVES.json')['passed'],os_identity_cases=os_cases,model_constructions=0,integrations=0,canonical_metadata_proxy_is_only_import_exercise=True,actual_MJB_metadata_required_in_new_stage=True,new24=0))
except BaseException as e:dump(Q/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);lock.close();dump(Q/'COMPLETION.json',dict(passed=passed,model_constructions=0,integrations=0,auditors_completed=len(rows)));print(json.dumps(read(Q/'COMPLETION.json')),flush=True)
