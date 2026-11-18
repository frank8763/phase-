"""Single finite software relay with immutable ninety-minute root."""
import sys,os,json,time,signal,hashlib,subprocess,fcntl,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1135_causal_batch';PY='/home/linghu/miniconda3/envs/mk_mujoco/bin/python'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not(O/'DRIVER_STARTED.json').exists();lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN);w={'started_unix':time.time(),'started_monotonic':time.monotonic(),'absolute_deadline_unix':time.time()+5400,'hard_stop_monotonic':time.monotonic()+5400,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'software_only':True,'physical_models_authorized':False};dump(O/'ROUND_WINDOW.json',w);dump(O/'DRIVER_STARTED.json',{'pid':os.getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time()});freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];rows=[];child=None;error=None;winner=None;table=None
 def remaining():
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'CROSS_BOOT_STOP';return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
 def storage():return sum(p.stat().st_size for p in O.rglob('*')if p.is_file()and not p.is_symlink())
 def terminate(*_):raise TimeoutError('ROOT_DEADLINE_OR_TERMINATION')
 def stopchild():
  nonlocal child
  if child and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def job(identifier,script,args,limit,output,result_name='COMPLETION.json'):
  nonlocal child
  assert remaining()>limit+90,'INSUFFICIENT_BOUNDED_REMAINDER';assert storage()+128*1024**2<2*1024**3,'NEW_BATCH_STORAGE_RESERVE';assert all(sha(R/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_CHANGED';assert(R/'REVIEW_PENDING').read_bytes()==guard,'PHYSICAL_GUARD_CHANGED';console=O/(identifier+'.console')
  with console.open('x')as log:
   child=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5',str(limit)+'s',PY,'-B',str(C/script),*map(str,args)],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',{'stage':identifier,'pid':child.pid,'proc_start':Path('/proc',str(child.pid),'stat').read_text().split()[21],'started_unix':time.time()})
   try:code=child.wait(timeout=min(limit+10,remaining()-60))
   finally:stopchild()
  p=output/result_name;result=json.loads(p.read_text())if p.exists()else None;row={'stage':identifier,'returncode':code,'output':str(output),'result':result};rows.append(row);dump(O/'RESULTS.json',rows)
  if code!=0 or not result:raise AssertionError('CHILD_OPERATION_OR_ACCOUNTING_FAILURE '+identifier)
  assert result.get('error')is None,'CHILD_MODEL_SOURCE_EVIDENCE_ERROR '+identifier
  assert result.get('models',0)==0 and result.get('physical_integrations',0)==0,'UNAUTHORIZED_MODEL'
  return result
 def run_candidate(item,script):
  out=O/item['id'];out.mkdir();item=dict(item,output=str(out),table=str(table),table_sha256=sha(table));file=O/(item['id']+'.json');dump(file,item);return job(item['id'],script,[file],625,out),out
 def audit_candidate(source,identifier):
  if remaining()<1600:return False,None
  out=O/(identifier+'_all8');out.mkdir();file=O/(identifier+'_all8.json');dump(file,{'output':str(out),'source':str(source),'table':str(table),'table_sha256':sha(table)});result=job(identifier+'_all8','audit_worker.py',[file],1525,out);return result['passed'],result
 signal.signal(signal.SIGTERM,terminate);signal.signal(signal.SIGINT,terminate);signal.signal(signal.SIGALRM,terminate);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()))
 try:
  assert json.loads((O/'BATCH_ENTRY_QUALIFICATION.json').read_text())['passed'];domain=job('domain','domain_worker.py',[O/'domain'],625,O/'domain','RESULT.json');assert domain['passed']and domain['all_dual_certificates_verified'];table=O/'domain/JOINT_TABLE.npz';dump(O/'TABLE_FREEZE.json',{'path':str(table),'sha256':sha(table),'qualified_source_input_sha256':domain['source_input_sha256']})
  phase,out=run_candidate({'id':'baseline40','seed':'saved','speed_factor':1.,'wait_seconds':0.},'phase_worker.py')
  if phase['passed']:
   ok,audit=audit_candidate(out,'baseline40')
   if ok:winner={'profile':'baseline40','seed':'saved','candidate_result':phase,'independent_all8_audit':audit}
  probes=json.loads((out/'PROBES.json').read_text());best=max(probes,key=lambda p:(p['passed'],p['minimum_timed_dynamic_m']));start_wait=best['initial_wait_native']*.01
  for item in json.loads((C/'PROFILES.json').read_text()):
   if winner:break
   if remaining()<725:break
   result,output=run_candidate(dict(item,wait_seconds=start_wait),'joint_worker.py')
   if result['passed']:
    ok,audit=audit_candidate(output,item['id'])
    if ok:winner={'profile':item['id'],'seed':item['seed'],'candidate_result':result,'independent_all8_audit':audit}
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',error)
 finally:
  stopchild();signal.setitimer(signal.ITIMER_REAL,0);dump(O/'ACTIVE.json',{'closed':True})
 summary={'closed':True,'passed_saved_software_component':winner is not None,'winner':winner,'stage_count':len(rows),'stages':[{'stage':r['stage'],'returncode':r['returncode'],'passed':r['result'].get('passed')if r['result']else None,'counts':r['result'].get('counts')if r['result']else None,'wall_s':r['result'].get('wall_s')if r['result']else None}for r in rows],'error':error,'wall_s':time.monotonic()-w['started_monotonic'],'root_deadline_unix':w['absolute_deadline_unix'],'models':0,'physical_integrations':0,'training_updates':0,'guard_original':(R/'REVIEW_PENDING').read_bytes()==guard,'source_unchanged':all(sha(R/p)==h for p,h in freeze.items()),'stage_access':False,'physical_route_or_fixed24_passed':False,'new_speed_physical_response_qualified':False,'no_automatic_physics_or_new_window':True,'stop_reason':'QUALIFIED_COMPONENT'if winner else'HARD_ERROR'if error else'FINITE_QUEUE_OR_ROOT_RESERVE','network_delivery_pending':True};dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary);report=R/'docs/RPCCR_CAUSAL_BATCH_V1135_REPORT.md';report.write_text('# V1135 finite causal software relay\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nThis is saved-state source development, not physical navigation, three-route regression or fixed24 acceptance. Coupled LP confidence set uses only original causal coefficient projections and the same public harmonic/Euclidean-speed class; each upper support has a retained dual certificate and interval guard. Any higher-speed proposal requires physical response qualification before use. No old windows or failures were reset.\n')
 cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur['active_zero_model_diagnostic']=None;cur['latest_software_experiment']={'version':'v1135','closed':True,'passed':winner is not None,'completion':str((O/'COMPLETION.json').relative_to(R)),'report':str(report.relative_to(R)),'physical_models':0,'physical_integrations':0};cur['next_physical_authorized']=False;dump(R/'CURRENT_EXPERIMENT.json',cur)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1135多步软件接力闭批：component='+str(winner is not None)+', stages='+str(len(rows))+', error='+str(error is not None)+', wall_s='+str(summary['wall_s'])+'；物理/模型/训练0，同版本三路线与24未执行；报告docs/RPCCR_CAUSAL_BATCH_V1135_REPORT.md。\n')
 manifest=[]
 for p in [*C.rglob('*'),*O.rglob('*'),report]:
  if p.is_file()and p.name not in ['campaign.console','LOCAL_MANIFEST.json']and not p.is_symlink():manifest.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)})
 dump(O/'LOCAL_MANIFEST.json',{'closed':True,'files':manifest,'source_readback_verified':all(sha(R/f['path'])==f['sha256']for f in manifest),'network_delivery_pending':True,'raw_retained':True,'models':0,'physical_integrations':0});print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
