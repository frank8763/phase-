"""Cheap metadata, real namespace guards, input assembly and budget before onceSOURCE."""
from common import *
import subprocess,zipfile,ast,traceback,fcntl

def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOFTWARE_PROOF.json').exists();v=dict(passed=False,closed=False,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physics=0,replay=0)
 try:
  from actors import SPECS
  weights={}
  for d,(n,h)in SPECS.items():
   p=R/n;assert sha(p)==h
   with zipfile.ZipFile(p)as z:
    data=json.loads(z.read('data'));assert data['policy_kwargs']==dict(net_arch=[256,256],use_sde=False)and not data['use_sde'];assert 'policy.pth'in z.namelist()
   weights[d]=dict(path=n,sha256=h,zip_metadata_only=True)
  locks=[]
  for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
   f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
  env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');ns=load('actual_guard_Phase_namespace',C/'namespace.py');guard=[]
  for n,cpu,marker in [('worker.py',2,'SCCR_TWO_ACTORS_NOT_ADMITTED'),('launch.py',5,'SOURCE_REMOTE_RECOVERY_NOT_READY'),('owner.py',5,'POST_SOURCE_STORAGE_BARRIER.json')]:
   args=ns.command(C/n,O)if cpu==2 else['/usr/bin/python3','-B',str(C/n)]
   p=subprocess.run(['taskset','-c',str(cpu),'nice','-n','19',*args],cwd=R,env=env,capture_output=True,timeout=15);assert p.returncode!=0 and marker.encode()in p.stderr,p.stderr[-1500:];guard.append(n)
  assert not(O/'WORKER_ONCE.json').exists()and not(O/'OWNER_ONCE.json').exists()and not(S/'LAUNCH_IDENTITY.json').exists()
  # Real frozen-actor entry rejects BEFORE importing Torch on a no-authority process.
  p=subprocess.run(['taskset','-c','2','nice','-n','19','/usr/bin/python3','-B',str(C/'guard_actor.py')],cwd=R,env=env,capture_output=True,timeout=15);assert p.returncode==0 and b'ACTOR_GUARD_BEFORE_TORCH'in p.stdout,p.stderr
  locks.clear()
  for p in C.glob('*.py'):ast.parse(p.read_text())
  from evidence import deliver
  for rid in [None,'POLICY']:compile(deliver(rid,preview=True),'prospective_dual_actor_transport','exec')
  from reservation import admission
  budget=admission()
  manifest=read(S/'ENVIRONMENT_READINESS.json');assert manifest['passed']and manifest['explicit_network_constructors']==manifest['forward_calls']==0
  for group in ['loaded_python_file_sha256','loaded_native_library_sha256']:
   for n,h in manifest[group].items():assert sha(n)==h,'READINESS_ENV_CHANGED'
  v.update(passed=True,weights=weights,production_guard_CLIs=guard,actor_refused_before_torch_import=True,real_namespace_worker_guard=True,budget=budget,source_commit_pending=True,environment_readiness_sha256=sha(S/'ENVIRONMENT_READINESS.json'),host_dependencies_are_exact_manifest_pins_not_self_contained_library_archive=True)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc())
 v['closed']=True;dump(S/'SOFTWARE_PROOF.json',v);print(json.dumps(v));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
