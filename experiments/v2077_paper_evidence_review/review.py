"""Saved evidence readout with three explicit levels of unfinished work."""
from pathlib import Path
import collections, copy, datetime, hashlib, json, os, time

R=Path(__file__).resolve().parents[2]
O=R/'runs/v2077_paper_evidence_review'
FIELDS=('case_id','course_id','dynamic','seed','phase','phase_design','start_xy','start_yaw','goal_xy','goal_yaw','speed','native_limit','stop_native','sensor_seed_unchanged','scope','historical_prefix_native','from_actual_native_zero')

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    start=time.monotonic();pins={}
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(p,expected=None):
        assert time.monotonic()-start<60
        h=sha(p)
        if expected is not None:assert h==expected,'BOUND_RESULT_CHANGED:'+str(p)
        pins[str(p.relative_to(R))]=h
        return json.loads(p.read_text())
    B=R/'runs/v1805_common_algorithm_registry'
    locked=read(B/'TASKS_METHODS_LOCKED.json')
    tasks={x['task']['task_id']:x['task']for x in locked['tasks']}
    slots=copy.deepcopy(read(B/'LEDGER.json')['slots'])
    for p in sorted((B/'PARALLEL_METHOD_EVENTS').glob('*.REGISTERED.json')):
        e=read(p);slot=next(s for s in slots if(s['method'],s['task_id'])==(e['method'],e['task_id']))
        assert not slot['registered'];slot.update(e)
        q=p.with_name(p.name.replace('.REGISTERED.json','.CLOSED.json'))
        if q.exists():
            e=read(q);assert e['registration_sha256']==sha(p);slot.update(e)
    rows=[];mismatches=[];scenes=collections.defaultdict(set)
    for slot in slots:
        row=dict(method=slot['method'],task_id=slot['task_id'],course=slot['case_id'])
        if not slot['registered']:kind='UNEXECUTED'
        elif not slot['closed']:kind='ACTIVE'
        elif slot.get('qualified_success'):kind='WHOLE_ARRIVAL'
        elif slot.get('valid_finite_method_refusal') or slot.get('status')=='VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT':kind='VALID_FINITE_REFUSAL'
        else:kind='TECHNICAL_CENSOR'
        row['outcome']=kind
        root=R/slot['root']if'root'in slot else(R/slot['result_path']).parent if slot.get('result_path')else None
        if slot['registered']:
            assert root is not None
            task=read(root/'PILOT_TASK.json');original=tasks[slot['task_id']]
            bad=[key for key in FIELDS if task.get(key)!=original.get(key)]
            if bad:mismatches.append(dict(method=slot['method'],task_id=slot['task_id'],fields=bad))
            row.update(task_fields_equal=not bad,direction=original['phase_design']['direction'])
        if slot['closed']:
            result=read(R/slot['result_path'],slot['result_sha256'])
            physical=result.get('physical')or{}
            first=result.get('machine_first_error')or result.get('first_error')or slot.get('first_error')or slot.get('technical_failure')
            row.update(first_error=first.get('error')if isinstance(first,dict)else first,
                       actual_native=result.get('actual_native'),replay_native=result.get('own_replay_native'),
                       final_goal_distance_m=physical.get('goal_distance_m'),minimum_actual_clearance_m=physical.get('minimum_actual_clearance_m'),
                       bad_contacts=physical.get('bad_contacts'),prefix_audit_passed=(result.get('independent_audit')or{}).get('passed'),
                       result_path=slot['result_path'])
            machine_path=root/'actual/RESULT.json'
            if machine_path.exists():
                machine=read(machine_path);scene=machine.get('scene_contract')or{}
                row.update(saved_live_scene_check_passed=scene.get('passed'),saved_original_contract=machine.get('original_contract'),
                           saved_training_updates=machine.get('training_updates'),saved_historical_controls=machine.get('historical_controls_used'),
                           recorded_modelwork_total=None)
                if scene.get('passed'):
                    identity=(scene.get('model_sha256'),scene.get('normalized_body_pos_sha256'))
                    scenes[slot['task_id']].add(identity)
            else:row['saved_machine_record_missing']=True
        rows.append(row)
    totals={entry['method']:dict(collections.Counter(x['outcome']for x in rows if x['method']==entry['method']))for entry in locked['methods']}
    rp=[x for x in rows if x['method']=='RP-CCR']
    by_course={k:dict(collections.Counter(x['outcome']for x in rp if x['course']==k))for k in dict.fromkeys(x['course']for x in rp)}
    ablation=read(R/'runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json')
    ablation_rows=[]
    for row in ablation['rows']:
        completion=read(R/row['completion_path'],row['completion_sha256'])
        ablation_rows.append(dict(assignment_id=row['assignment_id'],variant=row['variant'],course=row['case_id'],closed=row['closed'],
                                  owner_passed=row.get('owner_passed'),model_result=row.get('model_result'),
                                  functional_result=row.get('functional_result'),independent_prefix_audit=row.get('independent_prefix_audit'),
                                  actual_native=row.get('actual_native'),replay_native=row.get('own_replay_native')))
    gaps=[dict(id='F1',topic='Baseline fairness',status='PARTIALLY_CHECKED',done='Compare registered tasks and saved live-scene records',remaining='Disclose method-specific control/speed/candidate limits and adapter changes; review meaningful algorithm execution and sensor applicability; no equalwork claim'),
          dict(id='R1',topic='RP-CCR boundaries',status='DESCRIPTIVE_RESULTS_AVAILABLE',done='Per-course success/refusal/technical table with exact source results',remaining='Explain saved branch decisions without treating technical censors or observational association as mechanism causation'),
          dict(id='R2',topic='Reliability',status='NOT_ESTABLISHED',done='7 whole successes from 12 locked common tasks; all failures retained',remaining='Freeze the final method and prospectively register fresh confirmation tasks with explicit engineering acceptance criteria; this readout does not start or select those tasks'),
          dict(id='M1',topic='Mechanism benefit',status='NOT_ESTABLISHED',done='Separate20 ablations closed; 8 qualified whole successes and original technical gaps retained',remaining='Need complete eligible paired evidence with the declared mechanism actually activated; existing clean successful identical traces show no observed gain on those phases; no failed-task retuning or outcome-selected rerun')]
    value=dict(closed=True,readout_passed=True,checked_local=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
               denominator=120,totals=totals,slots=rows,fairness=dict(compared_fields=FIELDS,registered_task_mismatches=mismatches,
               saved_scene_identity_conflicts={k:[list(v)for v in values]for k,values in scenes.items()if len(values)>1},
               full_method_fairness_independently_proven=False,equal_total_compute_proven=False),
               RPCCR_by_course=by_course,ablation=dict(registered=ablation['registered_assignments'],closed=ablation['closed_assignments'],
               whole_successes=ablation['closed_successful_assignments'],unknown_native_counts=ablation['closed_native_counts_unknown_assignments'],rows=ablation_rows,mechanism_benefit_established=False),
               remaining_work=gaps,models=0,physics=0,replay=0,optimizer_calls=0,new_safety_audit=False,input_hashes=pins)
    assert all(sha(R/n)==h for n,h in pins.items()),'INPUT_CHANGED_DURING_REVIEW'
    O.mkdir(exist_ok=True);assert not(O/'RESULT.json').exists()
    raw=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n';assert len(raw.encode())<512*1024
    (O/'RESULT.json').write_text(raw)
    print(json.dumps({k:value[k]for k in ['checked_local','totals','fairness','RPCCR_by_course','remaining_work']},ensure_ascii=False))

if __name__=='__main__':main()
