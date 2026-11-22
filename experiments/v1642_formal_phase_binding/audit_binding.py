"""New-phase provenance and declared ablation prefix; original safety math."""
from pathlib import Path
from context import R,C,OLD,load

def audit(task,functional,source):
 assert task['case_id']=='WEST_EAST'and task['scope']=='same_known_course_new_phase_only'
 assert task['mechanism_variant']in {'full','no_onward'}and task['formal_assignment_id']
 assert functional['actual_original_goal_reached']and functional['passed']
 assert functional['passed_means_functional_navigation_only']and not functional['scientific_passed']
 target=Path(task['output'])/'RESULT.json';touched=[];seam_proofs=[]
 seams=load('v1642_explicit_audit_seams',C/'audit_seams.py')
 def bind_reader(module):
  if hasattr(module,'read'):
   original=module.read
   def read(path):return functional if Path(path)==target else original(path)
   module.read=read
  if hasattr(module,'load'):
   original_load=module.load
   def nested(name,path):return bind_reader(original_load(name,path))
   module.load=nested
  path=Path(getattr(module,'__file__','')).resolve()
  if path==seams.PARENT:seam_proofs.append(seams.fresh_phase_auditor(module,source))
  if path==seams.ADMISSION:seam_proofs.append(seams.bind_admission(module,source,task['mechanism_variant']))
  touched.append(str(path));return module
 module=bind_reader(load('v1642_original_full_auditor',OLD/'native_audit.py'));result=module.audit(task)
 assert result['passed']and len(seam_proofs)==2
 return dict(result,fresh_phase_provenance_rule_explicit=True,ablation_prefix_goal_only=True,
             all_original_current_safety_numeric_gates_retained=True,
             functional_input_separate_from_final_result=True,source_bindings=touched,
             seam_proofs=seam_proofs,formal_assignment_id=task['formal_assignment_id'])


def audit_kind(result):
 n=result.get('new_actual_native')
 if not(result.get('evidence_saved')and(result.get('replay')or{}).get('passed')and type(n)is int and n>0 and result.get('fully_recorded_native')==n):return 'unreviewable'
 if result.get('actual_original_goal_reached')and result.get('first_error')is None:return 'full_goal'
 return 'prefix_safety_only'

def audit_prefix(task,result,source):
 assert audit_kind(result)=='prefix_safety_only'
 # A distinct safety-only input satisfies the original auditor's functional
 # status convention; canonical first_error/RESULT is never cleared or replaced.
 scratch=dict(result,passed=False,error=None,functional_failure=dict(reason='PREFIX_SAFETY_ONLY_NOT_ARRIVAL',original_error=result.get('first_error')),
              scientific_passed=False,passed_means_functional_navigation_only=False)
 module=load('v1642_unchanged_actual_prefix_audit',R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py')
 path=Path(task['output'])/'PREFIX_SAFETY_AUDIT.json'
 answer=module.audit(task,result_override=scratch,output_path=path)
 assert answer['passed']and answer['safety_evidence_only']and not answer['functional_passed']
 return dict(answer,not_whole_goal_pass=True,canonical_first_error_preserved=True,
             original_numeric_actual_prefix_gates_unchanged=True)
