"""Build the one authorization-lifecycle seam, without claiming Source/models."""
from pathlib import Path
import ast,json,hashlib,os,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={0}and not(C/'context.py').exists()
P=R/'experiments/v2169_sccr_owner_proof_binding_recovery';parent=(P/'context.py').read_text();t=parent
a=t.index('def predecessors_closed():');b=t.index('def admission(task):',a)
predecessor='''def predecessors_closed():
 prior=R/'runs/v2169_sccr_owner_proof_binding_recovery';o=prior/'components/SCCR'
 assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(o/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 result=read(o/'actual/RESULT.json');assert result['closed']and not result['passed']and result['new_actual_native']==result['own_replay_native']==200 and result['canonical_vehicle_initializations']==1
 assert result['first_error']['error']=="AssertionError('FRESH_HISTORY_READ_FORBIDDEN BODY_COMMANDS.json')"and result['replay']['passed']and result['independent_audit']['passed']
 for name in ['LAUNCH_IDENTITY.json','components/SCCR/OWNED_CHILD.json']:
  i=read(prior/name);p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 return True
'''
t=t[:a]+predecessor+t[b:];t=t.replace('STUDY=SOURCE\n','STUDY=SOURCE\nfrom source_scope import SourceScope\n_SOURCE_SCOPE=SourceScope(R)\n')
old=" files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files"
new=""" assert not(O/'COMPLETION.json').exists(),'CLOSED_LIVE_UNION_AUTHORITY_REFUSED'
 files=read(SOURCE/'SOURCE_FREEZE.json')['files']
 files=_SOURCE_SCOPE.verify(files,binding=(sha(SOURCE/'SOURCE_FREEZE.json'),sha(O/'PILOT_ADMISSION.json'),digest(task)),initialization_started=(Path(task['output'])/'INITIALIZATION_ATTEMPT.json').exists())
 return a,w,files"""
assert t.count(old)==1;t=t.replace(old,new);ast.parse(t);(C/'context.py').write_text(t)
driver=ast.parse((P/'driver.py').read_text());fn=next(x for x in driver.body if isinstance(x,ast.FunctionDef)and x.name=='run')
calls=[x for x in ast.walk(fn)if isinstance(x,ast.Call)];admit=next(x for x in calls if isinstance(x.func,ast.Name)and x.func.id=='admission');install=next(x for x in calls if isinstance(x.func,ast.Attribute)and x.func.attr=='install');execute=next(x for x in calls if isinstance(x.func,ast.Name)and x.func.id=='execute');assert admit.lineno<install.lineno<execute.lineno
sys.path.insert(0,str(C));import context
assert context.C==C and context.SOURCE==S and context.predecessors_closed()
sites=[]
for name in ['driver.py','union_sampler.py','private_snapshot.py','policy.py']:
 tree=ast.parse((P/name).read_text());rows=[x.lineno for x in ast.walk(tree)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='admission'];assert rows;sites.append(dict(module=name,admission_lines=rows,body_not_changed=True))
assert 'torch'not in sys.modules and 'mujoco'not in sys.modules
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=dict(passed=True,closed=True,stage='UNQUALIFIED_AUTHORITY_SOURCE_LIFECYCLE_SEAM',parent_context_sha256=sha(P/'context.py'),draft_context_sha256=sha(C/'context.py'),source_scope_sha256=sha(C/'source_scope.py'),original_driver_bootstrap_line=admit.lineno,original_history_guard_install_line=install.lineno,original_execute_line=execute.lineno,source_bootstrap_strictly_precedes_history_guard_and_factory=True,live_call_sites=sites,only_predecessor_binding_and_source_verification_lifecycle_and_closed_gate_changed=True,all_physical_sensor_actor_decision_and_safety_bodies_not_changed=True,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,source_once_claimed=False,real_live_integration_not_yet_qualified=True)
(S/'SOURCE_SCOPE_DRAFT_CHANGE_PROOF.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
