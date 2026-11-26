from pathlib import Path
import hashlib,json,os,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2064_five_algorithm_parallel_math';H=R/'experiments/v2064_five_algorithm_parallel_math/evidence.py';RID='five_parallel_math'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def command(stage,args,cap):
 put(D/'PROGRESS.json',dict(stage=stage,unix=time.time()))
 with(D/(stage+'.console')).open('xb')as f:
  p=subprocess.Popen(['taskset','-c','5',*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=f,stderr=subprocess.STDOUT);put(D/'ACTIVE_STAGE.json',dict(stage=stage,pid=p.pid,start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],unix=time.time()));return p.wait(timeout=cap)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists()and not(S/'OWNER_ONCE.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];put(D/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),algorithm='PRIEST+PSF+PCBF',CPU7_PRIEST=True,CPU2_FILTERS=True,one_component_batch_only=True,models=0,formal_common_tasks=0));result=dict(closed=False,pipeline_passed=False,first_error=None,models=0,formal_common_tasks=0);start=time.monotonic()
 try:
  result['owner_returncode']=command('owner',['/usr/bin/python3','-B',str(R/'experiments/v2064_five_algorithm_parallel_math/owner.py')],650);assert read(S/'COMPLETION.json')['closed']
  for stage,args,cap in [('archive',['archive',RID],120),('ref',['ref',RID],15),('remote',['deliver',RID],620)]:assert command(stage,['/usr/bin/python3','-B',str(H),*args],cap)==0,'PARALLEL_MATH_EVIDENCE_STAGE_FAILED:'+stage
  T=S/'runtime_archives'/RID;assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];x=read(S/'COMPLETION.json');paths=[S/'COMPLETION.json',S/'priest_output/RESULT.json',S/'filter_output/RESULT.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json'];put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,mathematical_components_passed=x['passed'],whole_navigation_passed=False,full_vehicle_safety_qualified=False,formal_common_tasks=0,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False));result.update(pipeline_passed=True,mathematical_components_passed=x['passed'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
