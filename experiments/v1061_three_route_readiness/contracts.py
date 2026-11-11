"""Canonical task identity and fail-closed three-route admission; no models."""
import json,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1061_three_route_readiness'
CASES=('WEST_EAST','NORTH_SOUTH','EAST_WEST')
SEEDS=(10010001,10010002,10010003)
PHASES=(.6573753567727383,3.673083947600074,.9511239917756753)
GOAL_YAWS=(0.,-math.pi/2,math.pi)
def validate_tasks(tasks):
 assert len(tasks)==6,'EXACT_SIX_MAIN_REPEAT_TASKS_REQUIRED';course=json.loads((C/'COURSE.json').read_text());assert course['user_selected']and course['new_course_not_original_task_success']
 for i,case in enumerate(CASES):
  meta=json.loads((O/(case+('_ACTIVE_T0_METADATA.json'if case=='EAST_WEST'else'_T0_METADATA.json'))).read_text());assert meta['packet']['native_tick']==0 and meta['packet']['sim_time']==0.,'TRUE_ZERO_METADATA_REQUIRED'
  for j,role in enumerate(['main','repeat']):
   t=tasks[2*i+j];assert t['course_id']==course['id'],'DECLARED_COURSE_MISMATCH';assert t['task_id']==role+'_'+case.lower()and t['case_id']==case,'REGISTERED_ORDER_CHANGED';assert t['seed']==SEEDS[i]and t['phase']==PHASES[i],'SEED_OR_PHASE_CHANGED';assert t['goal_xy']==meta['goal']and t['start_xy']==meta['packet']['body'][:2]and t['start_yaw']==meta['packet']['body'][2],'CANONICAL_POSE_OR_GOAL_CHANGED';assert t['goal_yaw']==GOAL_YAWS[i],'GOAL_YAW_CHANGED';assert t['dynamic']is True and t['from_actual_native_zero']is True,'FRESH_DYNAMIC_TASK_REQUIRED';assert Path(t['output']).resolve().is_relative_to(R/'runs/v858_nav2_verified/v1061'),'OUTPUT_SCOPE'
 assert len({t['output']for t in tasks})==6,'DUPLICATE_OUTPUT'
 return True

def readiness(tasks,static,publication,contract,ns_software):
 validate_tasks(tasks);software=publication['passed']and contract['passed']and ns_software['passed']and ns_software['within_original8s_hold_budget'];rows=[]
 for case in CASES:
  row=static[case];independent=json.loads((O/'INDEPENDENT_SOFTWARE_AUDIT.json').read_text());saved_math=bool(case=='WEST_EAST'and independent['passed']and any(r.get('case')=='WE_CLASSIC_PRODUCER_UNCHANGED'and r.get('passed')for r in independent['rows']));ok=bool(row['passed']and row['audit']['passed']and row['plan']['status']=='COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED');rows.append(dict(case_id=case,static_complete_source_passed=ok,saved_real_measurement_producer_math_qualified=saved_math,requires_online_dynamic_source_certification_after_actual_discovery=True,actual_route_dynamic_source_qualified=False,new_version_physical_full_chain_passed=False,reason=None if ok else row['plan']['status']))
 return dict(preparation_checks_passed=bool(software),route_admission_passed=bool(software and all(x['static_complete_source_passed']for x in rows)),static_and_software_admission_only=True,ready_for_physics=False,models_authorized=False,rows=rows,new_physical_tasks_executed=0,new24_executed=0,models=0,integrations=0)

def launch_physics(*args,**kwargs):
 raise PermissionError('USER_SELECTED_SOURCE_AND_ZERO_MODEL_QUALIFICATION_ONLY')
