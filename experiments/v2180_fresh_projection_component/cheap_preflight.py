"""No source claim: exact inherited safety bodies, real admission refusals, ABI widths."""
from context import R,C,SOURCE as S,O,read,put,sha
import ast,os,subprocess,json,sys
assert os.sched_getaffinity(0)=={5}and not(S/'CHEAP_INTERFACE_PROOF.json').exists()and not(S/'SOURCE_ONCE.json').exists()
info=read(S/'INHERITED_RUNTIME_MODULES_DRAFT.json');parent=R/'experiments/v2176_sccr_common_plant_component';identical=[]
for n in info['exact']:assert(C/(n+'.py')).read_bytes()==(parent/(n+'.py')).read_bytes();identical.append(n)
for n in ['pilot_entry.py','run_phase.py','owner.py','launch.py']:
 t=(C/n).read_text();assert "'SCCR'"not in t and '==10'not in t,n
for n in ['owner.lock','execution.lock']:assert(O/n).is_file()
assert(S/'dispatch.lock').is_file()
for p in C.glob('*.py'):ast.parse(p.read_text())
# Full actual entry/read-only peer/launcher must stop before numerical imports,
# child spawn, once-claim or constructors. No attempt to import physical stack.
rows=[]
for n,cpu,token in [('pilot_entry.py',2,'FILTER_COMPONENT_NOT_ADMITTED'),('run_phase.py',2,'FILTER_INDEPENDENT_PHASE_NOT_ADMITTED'),('launch.py',5,'SOURCE_REMOTE_RECOVERY_NOT_READY'),('peer_entry.py',6,'PROJECTION_OPTIMIZER_ADMISSION.json')]:
 q=subprocess.run(['taskset','-c',str(cpu),'python3','-B',str(C/n)],cwd=R,env=dict(os.environ,PHASE_FILTER_METHOD='PROJ',PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=15)
 assert q.returncode!=0 and token.encode()in q.stdout+q.stderr,(n,q.stdout,q.stderr);rows.append(dict(entry=n,CPU=cpu,returncode=q.returncode,stderr=q.stderr.decode(),stdout=q.stdout.decode()))
assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])and not(S/'DISPATCH_ONCE.json').exists()
import evidence
for rid in [None,'PROJ']:
 text=evidence.deliver(rid,preview=True);compile(text,'new_orientation_delivery_preview','exec');assert 'phase-v2180-fresh-projection-component-20261127'in text and 'phase-v2176'not in text
from reserved_census import admission
b=admission();task=read(O/'PILOT_TASK.json');assert task['maximum_control_native']==120 and task['maximum_plans']==49 and task['maximum_current_native_queries']==1 and task['goal_xy']==[4.,-2.]
# All numerical libraries from actual readonly C2177 import already SHA-pinned
# in inherited source, with unchanged site; no duplicate numerical import suite.
proof=read(R/'runs/v2177_priest_vector_orientation/DEPENDENCY_IMPORT_PROOF.json');assert proof['passed']and proof['imported_exact_SciPy_modules']==289
for n,h in proof['source_files'].items():assert sha(R/n)==h
x=dict(passed=True,byte_identical_safety_physical_capture_replay_modules=identical,real_entry_refusals=rows,all_source_AST=True,all_lockfiles_precreated=True,new_transport_preview_compiles=True,dependency_real_import_proof_reused_by_exact_SHA=True,qualified_SciPy_import_modules=289,resource=b,models_NLP_physics_Source=0);put(S/'CHEAP_INTERFACE_PROOF.json',x);print(json.dumps({k:v for k,v in x.items()if k!='real_entry_refusals'}))
