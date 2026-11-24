"""Fresh-phase provenance and ablation-local prefix goal; original math unchanged."""
import ast,copy,hashlib,types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
PARENT=R/'experiments/v1281_partial_reconnection_fixed24/ns_audit.py'

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
 matches=[n for n in fn.body if isinstance(n,ast.If)and ast.unparse(n.test)=="task['slot'] == 13"]
 assert len(matches)==1,'OLD_NS_SAME_PHASE_PREFIX_SEAM_CHANGED'
 old=matches[0];assert 'runs/v858_nav2_verified/v1243/main_slot13' in ast.unparse(old)
 before=ast.dump(fn,include_attributes=False);index=fn.body.index(old);fn.body.remove(old)
 restored=copy.deepcopy(fn);restored.body.insert(index,copy.deepcopy(old))
 assert ast.dump(restored,include_attributes=False)==before,'UNRELATED_NS_AUDIT_CHANGED'
 namespace=vars(module).copy()
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(Path(__file__)),'exec',dont_inherit=True),namespace)
 module.audit=namespace['audit']
 return dict(removed_only_historical_same_phase_prefix_comparison=True,original_current_source_and_all_numeric_gates_retained=True,all_other_original_audit_AST_unchanged=True,original_source_sha256=hashlib.sha256(PARENT.read_bytes()).hexdigest(),transformed_audit_AST_sha256=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest())
