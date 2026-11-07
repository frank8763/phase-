"""Prepare one targeted repair and five fixed development tasks; zero models."""
import ast,json,shutil
from pathlib import Path
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/overnight_recovery_20261105'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
old=repo/'experiments/v828_goal_dynamic_confirmation';own=repo/'experiments/v830_ranked_return_development'
assert not own.exists();own.mkdir();(repo/'runs'/own.name).mkdir()
for p in old.glob('*.py'):
 if p.name not in ['execute.py','finalize.py']:shutil.copy2(p,own/p.name)
for name in ['KNOWN_FIELD.json','SCENE_CASES.json']:shutil.copy2(old/name,own/name)
p=own/'run_static.py';p.write_text(p.read_text().replace("'v828_goal_dynamic_confirmation'",repr(own.name)))
original=read(repo/'experiments/v812_soft_global_reference/DEVELOPMENT_TASKS.json');failed=read(old/'TASK_LIST.json')
tasks=[]
for slot,t in enumerate([failed[1],failed[7],original[1],original[0],original[2]],1):
 task=dict(t);task.update(slot=slot,development_role='previous_confirmation_failure'if slot<=2 else'original_three_route');tasks.append(task)
dump(own/'TASK_LIST.json',tasks);dump(own/'DEVELOPMENT_TASKS.json',tasks)
p=own/'audit_field_preflight.py';s=p.read_text();assert 'len(details)==len(tasks)==24'in s;p.write_text(s.replace('len(details)==len(tasks)==24','len(details)==len(tasks)==5'))
config=dict(label=own.name,output='runs/'+own.name,window='development01',confirmation=False,
 absolute_deadline_unix=read(repo/'RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json')['absolute_deadline_unix'],batch_cap_s=36000,
 minimum_start_budget_s=24000,repeat_slots=[1,2,3,4,5],reference_pair=None,
 reference_view='runs/overnight_recovery_20261105/qualification/reference/paired',report='docs/RPCCR_RANKED_RETURN_V830_REPORT.md',archive='evidence/rpccr_ranked_return_v830_20261105')
dump(own/'BATCH.json',config)
(own/'execute.py').write_text("from pathlib import Path\nimport sys\nown=Path(__file__).resolve().parent\nsys.path.insert(0,str(own.parent/'overnight_recovery_20261105'))\nfrom runner import run\nrun(own)\n")
(own/'finalize.py').write_text("from pathlib import Path\nimport sys\nown=Path(__file__).resolve().parent\nsys.path.insert(0,str(own.parent/'overnight_recovery_20261105'))\nfrom finalizer import finalize\nfinalize(own)\n")
(own/'PROTOCOL.md').write_text('''# V830: ranked return development, one offline bounded night

User2026-11-05 explicitly requested continued unattended overnight experiments after V828 failed. This is a new independent round, hard model/integration cutoff2026-11-06 08:00+0800 /1793923200; no reset or extension, all previous failures/sources/deadlines immutable. One scientific candidate, zero post-freeze repair/retry. No new confirmation pool or confirmation navigation tonight.

V829 saved527 seam reproduces original top1 return skipping seven progress-eligible forecasts. This proves search incompleteness, not native feasibility. The sole scientific change is to examine original nominal candidates in unchanged score order, retain original predicted goal progress>=.02, deduplicate identical first controls after progress filtering, and require the existing complete8+320/328 causal admission for each. Stop at first fully certified input; failed/shadow attempts retain original contract. All original action libraries/scoring/A*/V826 reference renewal/controller/network/noise/models unchanged. No added speed/actions and no safety relaxation. Additional independent ranked-return audit must reconstruct each saved forecast/progress/order/dedup and accepted applied command/certificate. Original13 auditors and full actual native replay remain mandatory.

Fixed development order: old V82810060002 phase3.1853003294397464 main and conditional full repeat; old10060008 phase3.2509695323644188 main/repeat; original NORTH_SOUTH10010002, WEST_EAST10010001, EAST_WEST10010003 each main/repeat. All five actualt0 preflights before navigation. At most5mains+5repeats. All are now development observations, not independent confirmation samples. First functional failure or any safety/source/model/truth/state/control/coverage/evidence anomaly stops remaining navigation. No substitutes, frozen repairs or additional candidates. Full repeat requires same outcome/length/model/initial state/real contact/discovery and qpos/qvel/ctrl/mocap<=1e-8.

Each navigation<=1200public,1200soft/1500hard/1505outer wall seconds;t0<=120/125. All model initialization/integration/private prediction/native replay only through run_phase, single CPU/single instance/execution lock. Subprocess full cap must fit absolute deadline; cutoff timer also terminates model process group. Training/SAC/realrobot0, Stage entirely isolated, no subagents/new chats/messages. Offline local process handles scheduling/gates/termination/auditing/report/archive, no network/chat dependency.

Original19 static entities/single diameter.20 amplitude.25 Euclidean speed.08actor/3m sensor5%dropout fixed. Truth only physical sensor and offline evaluation. Predetection static contract remains weaker reactive condition/public3m startup prior. Actual moving discovery—328 actual brake—new causal route—continued>=1m—goal<=.45 chain required; every native>=.15, obstacle/penetration/unknown0, full self/ctrl/rates/static geometry/no external root writes; original329execution657planning and all complete tails unchanged. No wider.12axis class/arbitrary occlusion/multiactor/map generality/realtime/recursive/RAS guarantee.

Finally restore exact REVIEW_PENDING, independently recheck persisted outputs/count exact or unknown, all-source/decompressedSHA archive and >90MiB blobs32MiB lossless reassembly before FINALIZED. Preserve all raw originals; no unattended network push and no old sync retry. Report qualification, old/new navigation/private/replay and unexecuted work separately. Five-route development success is not new24 dynamic acceptance.
''')
for name in ['worker_entry.py','evidence_rules.py','runner.py','finalizer.py']:
 shutil.copy2(repo/'experiments/goal_acceptance_20261105'/name,common/name)
print(json.dumps(dict(prepared=own.name,tasks=tasks,models=0)))
