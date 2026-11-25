from pathlib import Path
import hashlib,json,time,os
R=Path(__file__).resolve().parents[2];O=R/'runs/v1982_rpp_night_queue_proposal'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{6});assert not(O/'PLAN_DRAFT.json').exists();registry=R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json';ledger=R/'runs/v1805_common_algorithm_registry/LEDGER.json';rows=[]
 before=sha(ledger);book=read(ledger);tasks=read(registry)['tasks']
 for i in range(2,13):
  key=f'common_{i:02d}';task=next(v['task']for v in tasks if v['task']['task_id']==key);slot=next(v for v in book['slots']if v['method']=='RPP'and v['task_id']==key);assert not slot['registered']and not slot['closed'];rows.append(dict(order=i-1,assignment=key+'__RPP',task=task,method='RPP',runtime_admitted=False,task_sha256=hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 assert sha(ledger)==before
 value=dict(proposal_only=True,models=0,launches=0,common01_never_repeated=True,registry_path=str(registry.relative_to(R)),registry_sha256=sha(registry),ledger_snapshot_sha256=before,assignments=rows,first_dependency='runs/v1978_rpp_first_common_round/POST_ROUND_STORAGE_BARRIER.json',dependency_closed=(R/'runs/v1978_rpp_first_common_round/POST_ROUND_STORAGE_BARRIER.json').exists(),new_task_aware_owner_qualification_required=True,production_ready=False,first_case_only_current_authority=True,automatic_successor_enabled=False,engineering_estimate_per_case_minutes=[30,90],engineering_estimate_is_not_measured=True,all11_rough_hours_without_IO=[5.5,16.5],all11_completion_tonight_not_guaranteed=True,CPU_models=2,CPU_geometry=4,CPU_preparation=6)
 (O/'PLAN_DRAFT.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(proposal_cases=len(rows),all_unclaimed=True,models=0,launches=0,ready=False)))
if __name__=='__main__':main()
