"""Disabled exact-acceleration runtime, no window/model launch."""
from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parents[2];P=R/'experiments/v1220_stop_reserve_confirmation';C=R/'experiments/v1222_exact_stop_confirmation';O=R/'runs'/C.name
C.mkdir();O.mkdir()
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for p in P.glob('*.py'):
 if p.name in ['qualify.py','start.py']:continue
 (C/p.name).write_text(p.read_text().replace('v1220_stop_reserve_confirmation',C.name).replace('v1220','v1222').replace('V1220','V1222'))
# Same live execution and stop policy, qualified goal package; only bind exact search.
s=(R/'experiments/v1219_stop_preserving_observer/live_entry.py').read_text().replace("_here/'candidate_observer.py'","R/'experiments/v1221_exact_stop_pruning/candidate_observer.py'").replace("_here/'stop_policy.py'","R/'experiments/v1219_stop_preserving_observer/stop_policy.py'").replace('phase_v1219','phase_v1222')
(C/'live_entry.py').write_text(s)
p=C/'route_dispatch.py';s=p.read_text().replace("path=R/'experiments/v1219_stop_preserving_observer/live_entry.py'","path=C/'live_entry.py'");p.write_text(s)
d=json.loads((P/'PARENT_BINDINGS.json').read_text());d['files'].pop('experiments/v1219_stop_preserving_observer/live_entry.py');d['files'][str((C/'live_entry.py').relative_to(R))]=hashlib.sha256((C/'live_entry.py').read_bytes()).hexdigest();write(C/'PARENT_BINDINGS.json',d)
(C/'ORIGINAL_TASK_LIST.json').write_bytes((P/'ORIGINAL_TASK_LIST.json').read_bytes());fixed=[t for t in json.loads((P/'TASKS.json').read_text())if not t['role'].startswith('development_')];dev=[]
for role in ['main','repeat']:
 t=dict(next(t for t in fixed if t['task_id']=='main_slot02'));t.update(task_id='repair_'+role+'_slot02',role='development_'+role,pair_key='repair_slot02',baseline_id='repair_main_slot02',phase_group='repair');dev.append(t)
tasks=dev+fixed
for t in tasks:
 t.update(run_root=str(O),output=str(R/'runs/v858_nav2_verified/v1222'/t['task_id']));write(C/('TASK_'+t['task_id']+'.json'),t)
write(C/'TASKS.json',tasks)
p=C/'worker_context.py';s=p.read_text().replace("if x['slot']==3","if x['slot']==2");s=s.replace("assert type(approval.get('window_seconds'))in[int,float] and 0<approval['window_seconds']<=10800,'BOUNDED_AUTH_WINDOW'","assert type(approval.get('window_seconds'))in[int,float] and 0<approval['window_seconds']<=18000,'BOUNDED_AUTH_WINDOW'")
s=s.replace("assert window['absolute_deadline_unix']<=1794823359.4265096 and window['hard_stop_monotonic']<=336484.411977153,'ORIGINAL_CEILING_CHANGED'","auth=read(O/'AUTHORIZATION.json')\n    assert window['absolute_deadline_unix']<=auth['absolute_ceiling_unix'] and window['hard_stop_monotonic']<=auth['monotonic_ceiling'],'NEW_2030_CEILING_CHANGED'")
p.write_text(s)
p=C/'campaign.py';s=p.read_text().replace("==8 and len(devpairs)==4","==2 and len(devpairs)==1");p.write_text(s)
for name in ['GOAL_AUDIT_QUALIFICATION.json','NATIVE_AUDIT_QUALIFICATION.json']:
 d=json.loads((R/'runs/v1220_stop_reserve_confirmation'/name).read_text());d['inherited_unchanged_science_from']='V1220';write(O/name,d)
for p in list((R/'runs/v1220_stop_reserve_confirmation').glob('*_STATIC_SOURCE.json'))+list((R/'runs/v1220_stop_reserve_confirmation/analytical_cache').glob('*')):
 if p.is_file():target=O/p.relative_to(R/'runs/v1220_stop_reserve_confirmation');target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
write(O/'APPROVAL.json',dict(models_authorized=False))
write(O/'AUTHORIZATION.json',dict(authorized=False,scope='exact_selection_acceleration_slot2_main_repeat_then_original_fixed24',user_instruction='下一步开始，然后运行到今天晚上八点半',temporary_bytes=2*1024**3,new_independent_window=True,previous_failed_windows_unchanged=True,scientific_revisions=0,no_replacements=True,repeat_slots=[1,9,17]))
print(C)
