"""Reproduce the exact old lookup; verify correction and all pre-child reads."""
from pathlib import Path
import ast,copy,json,hashlib,os,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'experiments/v2168_sccr_live_union';PS=R/'runs/v2168_sccr_live_union'
assert os.sched_getaffinity(0)=={0}and not(S/'OWNER_BINDING_REGRESSION.json').exists()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(P/'owner.py').read_text();new=(C/'owner.py').read_text()
assert old.replace("assert read(SOURCE/'COMPONENT_INTERFACE_PROOF.json')['passed']","assert read(R/'runs/v2168_sccr_live_union/PHYSICAL_SEAM_PROOF.json')['passed']")==new
cases=[]
for label,path,token in [('old',P/'owner.py','COMPONENT_INTERFACE_PROOF'),('corrected',C/'owner.py','PHYSICAL_SEAM_PROOF')]:
 fn=copy.deepcopy(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='main'))
 guard=next(n for n in fn.body if isinstance(n,ast.Assert)and token in ast.unparse(n))
 # Keep the entire original tail unreachable so real local bindings survive;
 # execute the minimized ACTUAL failing call-site, no lock/model/child code.
 fn.body=[copy.deepcopy(guard),ast.Return(ast.Constant('OWNER_PROOF_BINDING_OK'))]+fn.body
 space=dict(R=R,SOURCE=PS,read=read);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec'),space)
 error=None;answer=None
 try:answer=space['main']()
 except FileNotFoundError as e:error=str(e);assert Path(e.filename)==PS/'COMPONENT_INTERFACE_PROOF.json'
 if label=='old':assert error and answer is None
 else:assert error is None and answer=='OWNER_PROOF_BINDING_OK'
 cases.append(dict(case=label,error=error,answer=answer,source_sha256=sha(path),full_original_tail_retained_unreachable=True))
# Verify every literal read in the actual pre-child prefix, without spoofing
# authority or claiming generated future source files already exist.
fn=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)and n.name=='main');future={'SOURCE_QUALIFICATION.json','POST_SOURCE_STORAGE_BARRIER.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','SOURCE_FREEZE.json','AUTHORIZATION.json'};dependencies=[]
for statement in fn.body:
 if 'out.mkdir'in ast.unparse(statement):break
 for n in ast.walk(statement):
  if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='read'and len(n.args)==1:
   expr=n.args[0];text=ast.unparse(expr)
   if isinstance(expr,ast.BinOp)and isinstance(expr.op,ast.Div)and isinstance(expr.left,ast.Name)and isinstance(expr.right,ast.Constant):
    root=expr.left.id;name=expr.right.value
    if root=='SOURCE':assert name in future;dependencies.append(dict(path='NEW_SOURCE/'+name,provenance='generated and remote-checked before launcher; no extra missing proof filename'))
    elif root=='R':assert(R/name).is_file();dependencies.append(dict(path=name,sha256=sha(R/name)))
    elif root=='O':assert(S/'components/SCCR'/name).is_file();dependencies.append(dict(path='NEW_COMPONENT/'+name,sha256=sha(S/'components/SCCR'/name)))
    else:raise AssertionError('UNCLASSIFIED_PRE_CHILD_READ:'+text)
   else:raise AssertionError('NONLITERAL_PRE_CHILD_READ_REQUIRES_INSPECTION:'+text)
assert any(n.get('path')=='runs/v2168_sccr_live_union/PHYSICAL_SEAM_PROOF.json'for n in dependencies)
sys.path.insert(0,str(C));import context
assert context.SOURCE==S and context.O==S/'components/SCCR'and context.C==C and context.predecessors_closed()
task=read(context.O/'PILOT_TASK.json');assert task['output']==str(context.O/'actual')and not(context.O/'actual').exists()
assert 'torch'not in sys.modules and 'mujoco'not in sys.modules
v=dict(passed=True,closed=True,red_old_missing_proof_and_green_corrected_actual_guard=True,cases=cases,all_pre_child_literal_read_dependencies=dependencies,new_source_and_component_root_binding_verified=True,old_failed_owner_not_reexecuted=True,original_owner_body_only_one_proof_lookup_change=True,models=0,renderer_constructors=0,NN_inference=0,physics=0,replay=0,source_once_claimed=False)
(S/'OWNER_BINDING_REGRESSION.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:x for k,x in v.items()if k not in ['cases','all_pre_child_literal_read_dependencies']}))
