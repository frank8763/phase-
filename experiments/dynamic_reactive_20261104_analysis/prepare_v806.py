"""Prepare one explicitly weaker, sensor-activated development condition. Zero models."""
import datetime, hashlib, json, pathlib, shutil, time
repo=pathlib.Path(__file__).resolve().parents[2]
base=repo/'experiments/v802_exact_rejection_global'
own=repo/'experiments/v806_sensor_activated_dynamic'
assert not own.exists()
own.mkdir()
for p in base.iterdir():
    if p.suffix in ('.py','.json') and p.name!='CANDIDATE_FREEZE.json':
        text=p.read_text().replace('v802_exact_rejection_global','v806_sensor_activated_dynamic')
        (own/p.name).write_text(text)
p=own/'motion_tracker.py';s=p.read_text()
old="""        if state['center']is None:
            from unseen_prior import clearance
            return np.minimum(values,clearance(field,poses,state,times))"""
assert s.count(old)==1
s=s.replace(old,"""        if state['center']is None:
            # V806 declared reactive condition: no universal unseen-actor proof.
            # No actor truth enters this function. Before first range detection,
            # this certificate covers known static geometry only.
            return values""")
p.write_text(s)
p=own/'run_static.py';s=p.read_text()
s=s.replace("if time.monotonic()-started>=780.","if time.monotonic()-started>=1200.")
anchor="    dump(out/'DYNAMIC_PROTOCOL.json',actor.config)"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    dump(out/'REACTIVE_SCOPE.json',{'version':'V806','actor_is_physical_scene_only':True,'before_first_range_detection':'KNOWN_STATIC_CERTIFICATE_ONLY','after_detection':'ORIGINAL_CAUSAL_UNION_FULL_328_CERTIFICATE','unseen_actor_robust_certificate_enforced':False,'arbitrary_occlusion_or_sudden_spawn_guarantee':False,'scene_truth_enters_online_policy':False,'physical_clearance_floor_m':.15,'prediction_floor_m':.155,'soft_wall_s':1200,'hard_wall_s':1500})")
anchor="                    install_time_gate(field,motion_state,a.dynamic_mode,circ,rect)"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n                    with (cell/'observed_actor_policy.jsonl').open('a') as stream:stream.write(json.dumps({'step':step,'time':float(env.data.time),'detected':motion_state['center']is not None,'gate_scope':'TRACKED_ACTOR_AND_STATIC'if motion_state['center']is not None else'KNOWN_STATIC_ONLY','scene_truth_input':False,'unseen_robust_guarantee':False})+'\\n')")
p.write_text(s)
tasks=json.loads((base/'DEVELOPMENT_TASKS.json').read_text())[:1]
(own/'DEVELOPMENT_TASKS.json').write_text(json.dumps(tasks,indent=2)+'\n')
now=time.time();auth=dict(version='V806',user_authorization='2026-11-04 user reviewed five static successes and explicitly requested physical-scene actor, lidar-triggered detection, replanning and continued dynamic experiments',started_preparation_unix=now,absolute_deadline_unix=now+7200,total_limit_s=7200,algorithm_conditions=1,maximum_actual_navigation=2,main_tasks=tasks,success_conditional_full_same_version_repeat=True,nav_public_cap=1200,nav_soft_wall_s=1200,nav_hard_wall_s=1500,nav_outer_wall_s=1505,fixture_retries_after_freeze=0,new_confirmation=0,old_deadlines_and_failures_preserved=True,training=0,stage_access=0,real_robot=0,scope='Limited sensor-activated reactive development; predetection certificate is static-only, deliberately not the old universal unseen-risk guarantee. No scene truth to online policy.')
(repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json').write_text(json.dumps(auth,indent=2,ensure_ascii=False)+'\n')
(repo/'RPCCR_SENSOR_ACTIVATED_LEDGER_20261104.json').write_text(json.dumps(dict(status='PREPARING_ZERO_MODEL_QUALIFICATION',round_closed=False,authorization='RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json',candidate_versions=1,nav_started=0,new_confirmation=0,original_static_five_closed=True,old_dynamic_batches_closed=True),indent=2)+'\n')
print(json.dumps({'prepared':str(own),'deadline_unix':auth['absolute_deadline_unix'],'new_models':0,'integrations':0}))
