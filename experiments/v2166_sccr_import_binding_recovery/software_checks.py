from common import *
import ast,subprocess,fcntl
assert os.sched_getaffinity(0)=={5}and not(S/'SOFTWARE_PROOF.json').exists()
P=R/'runs/v2165_sccr_dual_actor_component';OLD=R/'experiments/v2165_sccr_dual_actor_component'
assert read(S/'PRELUDE_BINDING_PROOF.json')['passed']and read(P/'components/POLICY/POST_POLICY_STORAGE_BARRIER.json')['passed']
for p in [P/'LAUNCH_IDENTITY.json',P/'components/POLICY/OWNED_CHILD.json']:
 i=read(p);stat=Path('/proc',str(i['pid']),'stat');assert not stat.exists()or stat.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
for name in ['actors','saved_inputs','namespace','environment_guard']:
 m=load('explicit_wrapper_'+name,C/(name+'.py'));assert Path(m._parent.__file__).resolve()==OLD/(name+'.py')
 if name=='actors':assert m.FrozenActor.__init__.__globals__['authority']is authority and m.FrozenActor.__init__.__globals__['R']==R
 if name=='environment_guard':assert m.PinnedLibraries.__init__.__globals__['S']==S
for name in ['owner','launch']:
 m=load('explicit_wrapper_'+name,C/(name+'.py'));assert m._parent.main.__globals__['S']==S and m._parent.main.__globals__['C']==C
locks=[]
for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
ns=load('new_bound_exact_Phase_namespace',C/'namespace.py');env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');guards=[]
for name,cpu,marker in [('worker',2,'SCCR_TWO_ACTORS_NOT_ADMITTED'),('owner',5,'POST_SOURCE_STORAGE_BARRIER.json'),('launch',5,'SOURCE_REMOTE_RECOVERY_NOT_READY')]:
 cmd=ns.command(C/(name+'.py'),O)if cpu==2 else['/usr/bin/python3','-B',str(C/(name+'.py'))]
 p=subprocess.run(['taskset','-c',str(cpu),'nice','-n','19',*cmd],cwd=R,env=env,capture_output=True,timeout=15);assert p.returncode!=0 and marker.encode()in p.stderr,p.stderr[-2000:];guards.append(name)
assert not(O/'OWNER_ONCE.json').exists()and not(O/'WORKER_ONCE.json').exists()
for name in ['ENVIRONMENT_READINESS.json','ENVIRONMENT_LAZY_DEPENDENCIES.json','LAZY_IMPORT_READINESS.json']:assert read(S/name)==read(P/name)
for p in C.glob('*.py'):ast.parse(p.read_text())
from reservation import admission
b=admission();from evidence import deliver
for rid in [None,'POLICY']:compile(deliver(rid,preview=True),'new_bound_source_transport','exec')
v=dict(passed=True,closed=True,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physical_native=0,old_failed_worker_not_relaunched=True,one_exact_import_binding_revision=True,original_numerical_modules_reused_by_identity=True,explicit_source_root_wrapper_bindings_verified=True,production_missing_admission_guards=guards,inherited_import_and_input_proofs_not_rerun={name:sha(P/name)for name in ['SOFTWARE_PROOF.json','SAVED_INPUT_SOFTWARE_PROOF.json','ENVIRONMENT_READINESS.json','LAZY_IMPORT_READINESS.json','ENVIRONMENT_GUARD_PROOF.json']},budget=b);dump(S/'SOFTWARE_PROOF.json',v);print(json.dumps(v))
