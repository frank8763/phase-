"""New-phase provenance and declared ablation prefix; original safety math."""
from pathlib import Path
import sys,importlib.machinery,hashlib,ast,copy,types
from context import R,C,OLD,load

def bind_local_directory(module,source,seams):
 path=Path(getattr(module,'__file__','')).resolve()
 if path.parent==OLD and path.name in {'native_audit.py','ew_audit.py','audit_time.py'}:
  assert not path.is_symlink() and source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'AUDITOR_DIRECTORY_SOURCE_IDENTITY'
  name='verify'if path.name=='audit_time.py'else'audit'
  seams.original_function(module,path,name)
  inherited=Path(module.C).resolve()
  assert inherited in {OLD,R/'experiments/v1271_ew_joint_phase_validation'},'UNEXPECTED_AUDITOR_DIRECTORY'
  before=getattr(module,name).__code__;module.C=path.parent
  assert getattr(module,name).__code__ is before,'DIRECTORY_BIND_CHANGED_FUNCTION'
  return dict(path=str(path.relative_to(R)),inherited=str(inherited.relative_to(R)),bound=str(path.parent.relative_to(R)),function_code_unchanged=True)
 return None

def bind_reader(module,target,functional,source,seams,touched,seam_proofs,variant='full'):
 binding=bind_local_directory(module,source,seams)
 if binding is not None:touched.append(binding)
 if hasattr(module,'read'):
  original=module.read
  def read(path):return functional if Path(path)==target else original(path)
  module.read=read
 if hasattr(module,'load'):
  original_load=module.load
  def nested(name,path):return bind_reader(original_load(name,path),target,functional,source,seams,touched,seam_proofs,variant)
  module.load=nested
 path=Path(getattr(module,'__file__','')).resolve()
 if path==seams.PARENT:seam_proofs.append(seams.fresh_phase_auditor(module,source))
 if path==seams.TIMING:seam_proofs.append(seams.time_eligibility_audit(module,source,variant))
 touched.append(str(path));return module

def audit(task,functional,source):
 assert task['case_id']=='EAST_WEST'and task['scope']=='same_known_course_new_phase_only'
 assert task['mechanism_variant']in {'full','no_time'}and task['formal_assignment_id']
 assert functional['actual_original_goal_reached']and functional['passed']
 assert functional['passed_means_functional_navigation_only']and not functional['scientific_passed']
 target=Path(task['output'])/'RESULT.json';touched=[];seam_proofs=[]
 seams=load('v1642_explicit_audit_seams',C/'audit_seams.py')
 module=bind_reader(load('v1765_original_full_auditor',OLD/'native_audit.py'),target,functional,source,seams,touched,seam_proofs,task['mechanism_variant']);result=module.audit(task)
 assert result['passed']and len(seam_proofs)==2
 return dict(result,fresh_phase_provenance_rule_explicit=True,EW_wait0_eligibility_only=True,
             all_original_current_safety_numeric_gates_retained=True,
             functional_input_separate_from_final_result=True,source_bindings=touched,
             seam_proofs=seam_proofs,formal_assignment_id=task['formal_assignment_id'])


def audit_kind(result):
 n=result.get('new_actual_native')
 if not(not result.get('model_native_inflight_unknown',False)and result.get('evidence_saved')and(result.get('replay')or{}).get('passed')and type(n)is int and n>0 and result.get('fully_recorded_native')==n):return 'unreviewable'
 if result.get('actual_original_goal_reached')and result.get('first_error')is None:return 'full_goal'
 return 'prefix_safety_only'

def prefix_import_scope(source):
 path=R/'experiments/v1195_eight_gib_timed_refuge/route_tools.py';directory=path.parent
 assert source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'PREFIX_IMPORT_SOURCE_CHANGED'
 resident=sys.modules.get('route_tools')
 if resident is not None:assert Path(resident.__file__).resolve()==path,'PREFIX_IMPORT_RESIDENT_CONFLICT'
 previous=sys.path[:];sys.path.insert(0,str(directory))
 try:
  spec=importlib.machinery.PathFinder.find_spec('route_tools',sys.path)
  assert spec is not None and Path(spec.origin).resolve()==path,'PREFIX_IMPORT_RESOLVER_MISMATCH'
 except BaseException:
  sys.path[:]=previous;raise
 return previous,dict(path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),original_parent_import_directory=True)

EARLY_ERROR="AssertionError('FIRST_DISCOVERY_NOT_NORMAL_DRIVING')"
def early_discovery_refusal(r,segments,journal,n,discovery,commands):
 original=r.get('functional_failure',{}).get('original_error')or{}
 if original.get('stage')!='normal'or original.get('error')!=EARLY_ERROR:return False
 assert n>=200 and discovery==n-200 and r['physical']['first_actor_detection']['native_tick']==discovery,'EARLY_DISCOVERY_NATIVE_BINDING'
 assert r['error_stop']['applied']==200 and r['error_stop_progress']['complete200']and r['error_stop_progress']['applied']==200,'EARLY_DISCOVERY_COMPLETE200_REQUIRED'
 assert len(journal)==len(commands)==n and journal[discovery-1]['request'][0]==0.,'DISCOVERY_WAS_NOT_STOPPED_REQUEST'
 assert all(row['applied']and row['before_native']==i and row['request']==[0.,0.,False]for i,row in enumerate(journal[discovery:],discovery)),'EARLY_DISCOVERY_ZERO_TAIL'
 assert not any(s['label']=='DISCOVERY_STOP'for s in segments),'EARLY_DISCOVERY_UNEXPECTED_STOP_STAGE'
 return True

def bind_refusal_stage(module,source):
 path=R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py'
 assert Path(module.__file__).resolve()==path and source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'EARLY_PREFIX_ORIGINAL_SOURCE_IDENTITY'
 expected=next(c for c in compile(path.read_bytes(),str(path),'exec',dont_inherit=True).co_consts if isinstance(c,types.CodeType)and c.co_name=='audit')
 def identity(c):return(c.co_code,c.co_names,c.co_flags,c.co_varnames,tuple(identity(v)if isinstance(v,types.CodeType)else v for v in c.co_consts))
 assert identity(module.audit.__code__)==identity(expected),'EARLY_PREFIX_ORIGINAL_FUNCTION_CHANGED'
 tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit');before=ast.dump(fn,include_attributes=False)
 matches=[n for n in fn.body if isinstance(n,ast.Assert)and "s['label'] == 'DISCOVERY_STOP'"in ast.unparse(n.test)];assert len(matches)==1
 old=matches[0];index=fn.body.index(old);guard=ast.parse('if not _early_discovery_refusal(r,segments,journal,n,discovery,commands):\n assert True').body[0];guard.body=[old];fn.body[index]=guard
 restored=copy.deepcopy(fn);restored.body[index]=copy.deepcopy(old);assert ast.dump(restored,include_attributes=False)==before,'UNRELATED_PREFIX_NUMERICAL_GATE_CHANGED'
 namespace=vars(module).copy();namespace['_early_discovery_refusal']=early_discovery_refusal
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(C/'audit_binding.py'),'exec',dont_inherit=True),namespace);module.audit=namespace['audit']
 return dict(original_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),only_stage_expectation_guarded_for_exact_early_refusal=True,all_original_other_numeric_scene_contact_source_replay_control_memory_finalstop_gates_unchanged=True)

def audit_prefix(task,result,source):
 assert audit_kind(result)=='prefix_safety_only'
 scratch=dict(result,passed=False,error=None,functional_failure=dict(reason='PREFIX_SAFETY_ONLY_NOT_ARRIVAL',original_error=result.get('first_error')),
              scientific_passed=False,passed_means_functional_navigation_only=False)
 previous,dependency=prefix_import_scope(source)
 try:
  module=load('v1646_unchanged_actual_prefix_audit',R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py')
  path=Path(task['output'])/'PREFIX_SAFETY_AUDIT.json'
  branch_proof=bind_refusal_stage(module,source)
  answer=module.audit(task,result_override=scratch,output_path=path)
 finally:sys.path[:]=previous
 assert answer['passed']and answer['safety_evidence_only']and not answer['functional_passed']
 return dict(answer,not_whole_goal_pass=True,canonical_first_error_preserved=True,
             original_numeric_actual_prefix_gates_unchanged=True,prefix_import_dependency=dependency,early_refusal_stage_scope=branch_proof)
