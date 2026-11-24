"""Fixed original DWA remainder; explicit new overnight window only."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1913_dwa_night_qualified'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
KEYS=['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction','native_limit','stop_native','speed']
def validate(plan,registry):
    assert plan['locked_total']==7 and len(plan['assignments'])==7
    assert plan['common_registry_sha256']==sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
    assert sha(R/plan['previous_plan_path'])==plan['previous_plan_sha256']
    old=read(R/plan['previous_plan_path'])['assignments']
    for i,row in enumerate(plan['assignments']):
        assert row['order']==i and row['method']=='DWA' and row['common_task']==f'common_{i+6:02d}'
        assert row['round_id']==row['common_task']+'__DWA' and row['production']=='v1912_dwa_hybrid_evidence'
        assert row['output_root']=='runs/v1913_dwa_night_qualified/rounds/'+row['round_id']
        prior=next(x for x in old if x['round_id']==row['round_id'])
        a=read(R/prior['output_root']/'PILOT_TASK.json');b=read(R/row['output_root']/'PILOT_TASK.json')
        assert {k:v for k,v in a.items()if k not in {'output','run_root'}}=={k:v for k,v in b.items()if k not in {'output','run_root'}}
        shared=next(x['task']for x in registry['tasks']if x['task']['task_id']==row['common_task'])
        for k in KEYS:assert b[k]==shared[k],'SCIENTIFIC_TASK_CHANGED:'+k
        for n in ['LIMITS_DRAFT.json','REFERENCE_CONFIG.json']:assert sha(R/prior['output_root']/n)==sha(R/row['output_root']/n)
    return True
def time_admission(auth,now,boot):
    assert auth['authorized'] and auth['boot_id']==boot
    assert auth['deadline_local']=='2026-11-25T09:00:00+08:00'
    assert auth['maximum_assignments']==7 and auth['maximum_round_s']==5400 and auth['normal_s']==4200 and auth['close_s']==1200
    assert auth['per_round_pipeline_reserve_s']==7200
    assert now+7200<auth['deadline_unix'],'NO_COMPLETE_PIPELINE_BEFORE_0900'
    return True
