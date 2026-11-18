"""Prepare disabled runtime; never creates models or a new physical window."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2];C=R/'experiments/v1220_stop_reserve_confirmation';O=R/'runs'/C.name
C.mkdir(exist_ok=False);O.mkdir(exist_ok=False)
old=R/'experiments/v1218_fixed24_current'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for name in ['worker.py','worker_context.py','route_dispatch.py','native_audit.py','native_audit_cli.py','audit.py','audit_admission.py','audit_refusal.py','campaign.py','campaign_context.py','t0.py','t0_audit.py','gates.py','watchdog.py','finish.py','check_cached_runtime.py']:
 s=(old/name).read_text().replace('v1218_fixed24_current',C.name).replace('v1218','v1220').replace('V1218','V1220');(C/name).write_text(s)
# Load the newly qualified live source explicitly. Its goal package is immutable V1218.
s=(C/'route_dispatch.py').read_text().replace("path=C/'live_entry.py'","path=R/'experiments/v1219_stop_preserving_observer/live_entry.py'");(C/'route_dispatch.py').write_text(s)
parent=json.loads((old/'PARENT_BINDINGS.json').read_text());parent['files'].pop('experiments/v1218_fixed24_current/live_entry.py');write(C/'PARENT_BINDINGS.json',parent)
pool=(old/'ORIGINAL_TASK_LIST.json').read_bytes();(C/'ORIGINAL_TASK_LIST.json').write_bytes(pool)
fixed=json.loads((old/'TASKS.json').read_text());dev=[]
# Same failed fixed slot is a development task; it never enters the 24 denominator.
for role in ['main','repeat']:
 t=dict(next(t for t in fixed if t['task_id']=='main_slot03'));t.update(task_id='repair_'+role+'_slot03',role='development_'+role,pair_key='repair_slot03',baseline_id='repair_main_slot03',phase_group='repair');dev.append(t)
for t0 in json.loads((R/'experiments/v1217_private_three_route/TASKS.json').read_text()):
 t=dict(t0);t.update(task_id='regression_'+t['task_id'],role='development_'+t['role'],pair_key=t['case_id'],baseline_id='regression_main_'+t['case_id'],phase_group='regression',slot=0,initial_axis_motion_direction='DEVELOPMENT_ONLY');dev.append(t)
tasks=dev+fixed
for t in tasks:
 t.update(run_root=str(O),output=str(R/'runs/v858_nav2_verified/v1220'/t['task_id']))
 write(C/('TASK_'+t['task_id']+'.json'),t)
write(C/'TASKS.json',tasks)
for name in ['GOAL_AUDIT_QUALIFICATION.json','NATIVE_AUDIT_QUALIFICATION.json']:
 p=R/'runs/v1218_fixed24_current'/name;d=json.loads(p.read_text());d['inherited_unchanged_part_only']=True;d['repair_audit_requires_separate_qualification']=True;write(O/name,d)
write(O/'APPROVAL.json',dict(models_authorized=False))
write(O/'AUTHORIZATION.json',dict(authorized=False,scope='repair_main_repeat_then_same_version_six_regression_then_conditional_fixed24',user_instruction='下一步修复通过继续24项的；继续',temporary_bytes=2*1024**3,original_absolute_ceiling=1794823359.4265096,original_monotonic_ceiling=336484.411977153,new_window_granted=False,scientific_revisions=1,no_replacements=True,repeat_slots=[1,9,17]))
print(C)
