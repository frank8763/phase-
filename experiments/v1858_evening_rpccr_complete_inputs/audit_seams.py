"""Fresh-phase provenance and ablation-local prefix goal; original math unchanged."""
import ast,copy,hashlib,types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
PARENT=R/'experiments/v1204_goal_audit_worker/native_audit.py'
ADMISSION=R/'experiments/v1281_partial_reconnection_fixed24/audit_admission.py'

def checked(path,sources):
 assert sources[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest()
 return path.read_text()

def code_identity(code):
 return(code.co_code,code.co_names,code.co_flags,code.co_varnames,tuple(code_identity(v)if isinstance(v,types.CodeType)else v for v in code.co_consts))

def original_function(module,path,name):
 assert Path(module.__file__).resolve()==path
 code=compile(path.read_bytes(),str(path),'exec',dont_inherit=True)
 expected=next(v for v in code.co_consts if isinstance(v,types.CodeType)and v.co_name==name)
 assert code_identity(getattr(module,name).__code__)==code_identity(expected),'ORIGINAL_AUDIT_FUNCTION_CHANGED'

def fresh_phase_auditor(module,sources):
 original_function(module,PARENT,'audit')
 tree=ast.parse(checked(PARENT,sources));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
 matches=[n for n in fn.body if isinstance(n,ast.If)and ast.unparse(n.test)=="task['seed'] in [10060001, 10060002]"]
 assert len(matches)==1,'OLD_SAME_PHASE_PREFIX_SEAM_CHANGED'
 old=matches[0];assert 'runs/v858_nav2_verified/v1185/main_slot'in ast.unparse(old)
 # This obsolete comparison assumes identical actor phase. It is a provenance
 # assertion, not a safety gate. Every current-state/source/physical/control/
 # replay/stop/goal assertion in all other original statements remains intact.
 fn.body.remove(old);namespace=vars(module).copy()
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(Path(__file__)),'exec',dont_inherit=True),namespace)
 answer=namespace['audit'];assert isinstance(answer,types.FunctionType)
 module.audit=answer
 return dict(removed_only_historical_same_phase_prefix_comparison=True,
             original_current_source_and_all_numeric_gates_retained=True,
             original_source_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),
             transformed_audit_AST_sha256=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest())

def prefix_proof_input(x,selection,reference,variant):
 assert variant in {'full','no_onward'}
 flagged=selection.get('measured_onward_still_required',False)
 if variant=='no_onward'and selection.get('method')=='refuge_onward':assert flagged is True,'ABLATION_PREFIX_SCOPE_FLAG_MISSING'
 if not flagged:
  assert variant!='full'or flagged is False

  assert not selection.get('prefix_counts_as_whole_arrival',False)
  return x
 assert variant=='no_onward'and selection['method']=='refuge_onward'
 assert selection['prefix_counts_as_whole_arrival']is False
 assert selection['prefix_rows']==selection['rows']and selection['prefix_native']==len(reference)-1
 assert all(type(row[2])is int and row[2]>0 for row in selection['rows'])and sum(row[2]for row in selection['rows'])==selection['prefix_native']
 assert selection['admission']['passed']and selection['admission']['shadow_memory_reset']is False
 local=copy.deepcopy(x);local['goal']=[float(v)for v in reference[-1,:2]]
 return local

def bind_admission(module,sources,variant):
 original_function(module,ADMISSION,'verify_source');checked(ADMISSION,sources)
 original=module.verify_source
 def verify_source(x,table,origin,shadow_origin,offset,selection,reference,deadline):
  local=prefix_proof_input(x,selection,reference,variant)
  # Reconstruct the declared prefix's original feedback/shadow/2200stop proof.
  # Final actual-task goal remains checked by the independent whole audit.
  return original(local,table,origin,shadow_origin,offset,selection,reference,deadline)
 module.verify_source=verify_source
 return dict(variant=variant,original_numeric_verify_source_unchanged=True,
             prefix_goal_only_for_flagged_no_onward=True,final_actual_task_goal_unchanged=True)


GOAL=R/'experiments/v1204_goal_audit_worker/audit_goal.py'
def bind_goal_verify_import(module,sources,variant):
 """Bind the imported verifier before the parent's audit globals are copied."""
 assert Path(module.__file__).resolve()==PARENT
 original=module.verify
 assert Path(original.__globals__['__file__']).resolve()==GOAL
 expected=next(v for v in compile(checked(GOAL,sources),str(GOAL),'exec',dont_inherit=True).co_consts if isinstance(v,types.CodeType)and v.co_name=='verify')
 assert code_identity(original.__code__)==code_identity(expected),'ORIGINAL_GOAL_VERIFY_CHANGED'
 tree=ast.parse(checked(GOAL,sources));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='verify')
 before=ast.dump(fn,include_attributes=False)
 loops=[n for n in fn.body if isinstance(n,ast.For)and ast.unparse(n.target)=='(index, offset)']
 assert len(loops)==1,'GOAL_SOURCE_GENERATION_LOOP_CHANGED'
 loop=loops[0];matches=[n for n in loop.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='proof']
 assert len(matches)==1 and ast.unparse(matches[0].value)=='q.proof(OffsetGeometry(geometry, offset), local, ss, uu, q.requests_of(rows), mm)','GOAL_SOURCE_PROOF_CALL_CHANGED'
 added=ast.parse("local = _v1744_prefix_input(local, selection, saved['states'], _v1744_variant) if index == 0 else local").body[0]
 loop.body.insert(loop.body.index(matches[0]),added)
 unchanged=copy.deepcopy(fn);copyloop=next(n for n in unchanged.body if isinstance(n,ast.For)and ast.unparse(n.target)=='(index, offset)');copyloop.body.pop(loop.body.index(added))
 assert ast.dump(unchanged,include_attributes=False)==before,'UNRELATED_GOAL_AUDIT_CHANGED'
 namespace=original.__globals__.copy();namespace.update(_v1744_prefix_input=prefix_proof_input,_v1744_variant=variant)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(Path(__file__)),'exec',dont_inherit=True),namespace)
 module.verify=namespace['verify']
 return dict(original_goal_verify_sha256=hashlib.sha256(GOAL.read_bytes()).hexdigest(),only_added_flagged_initial_prefix_goal_input=True,all_other_original_verify_AST_unchanged=True,whole_actual_goal_and_onward_checks_unchanged=True,variant=variant,transformed_verify_AST_sha256=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest())
