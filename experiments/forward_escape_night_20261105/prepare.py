"""Prepare one return-only appended tail library and fixed saved qualification."""
import ast,copy,json,shutil
from pathlib import Path
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/forward_escape_night_20261105';old=repo/'experiments/v830_ranked_return_development';own=repo/'experiments/v832_forward_escape_development';probe=repo/'experiments/v831_forward_escape_qualification'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
assert not own.exists();own.mkdir();(repo/'runs'/own.name).mkdir()
for p in old.iterdir():
 if p.is_file()and p.suffix in['.py','.md','.json']and p.name!='CANDIDATE_FREEZE.json':shutil.copy2(p,own/p.name)
for p in (repo/'experiments/overnight_recovery_20261105').glob('*.py'):
 if p.name not in ['prepare.py','register.py','freeze.py','verify_ops.py']:shutil.copy2(p,common/p.name)
for p in common.glob('*.py'):
 if p.name in ['prepare.py','register.py']:continue
 s=p.read_text().replace('overnight_recovery_20261105','forward_escape_night_20261105').replace('v830_ranked_return_development','v832_forward_escape_development').replace('RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json','RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json').replace('V830','V832').replace('RPCCR_OVERNIGHT_RECOVERY_20261105','RPCCR_FORWARD_ESCAPE_NIGHT_20261105')
 p.write_text(s)
p=own/'run_static.py';p.write_text(p.read_text().replace("'v830_ranked_return_development'",repr(own.name)))
for name in ['execute.py','finalize.py']:
 p=own/name;p.write_text(p.read_text().replace('overnight_recovery_20261105','forward_escape_night_20261105'))
cfg=read(own/'BATCH.json');cfg.update(label=own.name,output='runs/'+own.name,minimum_start_budget_s=21600,reference_view='runs/forward_escape_night_20261105/qualification/reference/paired',report='docs/RPCCR_FORWARD_ESCAPE_V832_REPORT.md',archive='evidence/rpccr_forward_escape_v832_20261105');dump(own/'BATCH.json',cfg)
p=own/'reserved_recovery.py';s=p.read_text()
s=s.replace('self.last_attempt=None;self.handovers=0;self.expected_ctrl=None','self.last_attempt=None;self.handovers=0;self.expected_ctrl=None;self.allow_forward_escape=False')
s=s.replace("        for library,choices in [('ORIGINAL',original),('FORWARD_EXTENSION',forward)]:\n            if library=='FORWARD_EXTENSION'and best is not None:break","        escape=[(steer,wheel)for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for wheel in [8.,12.]]\n        groups=[('ORIGINAL',original),('FORWARD_EXTENSION',forward)]\n        if self.allow_forward_escape:groups.append(('RETURN_FORWARD_ESCAPE',escape))\n        for library,choices in groups:\n            if library!='ORIGINAL'and best is not None:break")
s=s.replace("kind='BRAKE_ONLY'if brake_only else'FORWARD_BRAKE'if wheel>0 else'REVERSE_BRAKE'","kind='BRAKE_ONLY'if brake_only else'FORWARD_ESCAPE_BRAKE'if library=='RETURN_FORWARD_ESCAPE'else'FORWARD_BRAKE'if wheel>0 else'REVERSE_BRAKE'")
s=s.replace("kind=='FORWARD_BRAKE'and signed<.02","kind in('FORWARD_BRAKE','FORWARD_ESCAPE_BRAKE')and signed<.02")
s=s.replace("signed if kind=='FORWARD_BRAKE'else-signed","signed if kind in('FORWARD_BRAKE','FORWARD_ESCAPE_BRAKE')else-signed")
s=s.replace('candidate=ReservedRecovery(self.predictor,self.mj,self.ids,self.cell)','candidate=ReservedRecovery(self.predictor,self.mj,self.ids,self.cell)\n        candidate.allow_forward_escape=True')
p.write_text(s);ast.parse(s)
# Auditors explicitly register the new finite schedule; all old clauses retained.
extra="or(kind=='FORWARD_ESCAPE_BRAKE'and brake==160 and tuple(target[2:])in[(8.,8.),(12.,12.)]and signed>=.02)"
for name in ['audit_run.py','audit_all_tail_geometry.py']:
 p=own/name;s=p.read_text();needle="or(kind=='FORWARD_BRAKE'and brake==240 and np.array_equal(target[2:],[4.,4.])and signed>=.02)";assert needle in s;s=s.replace(needle,needle+extra);p.write_text(s)
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';cell=pair/'geometry_memory';decisions=[json.loads(x)for x in(cell/'control_decisions.jsonl').open()];states={}
for x in map(json.loads,(cell/'motion_estimate.jsonl').open()):
 if x['step']in[495,527]:states[x['step']]={k:v for k,v in x.items()if k!='step'}
inputs=[]
for step in[495,527]:
 n=next(x for x in decisions if x['step']==step and x['candidate_role']=='BACKUP_RETURN'and x['stage']=='NOMINAL');ranked=sorted([c for c in n['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True)
 attempts=[x for x in decisions if x['step']==step and x['candidate_role']=='BACKUP_RETURN'and x['stage']=='BACKUP_APPEND']
 inputs.append(dict(step=step,state=states[step],nominal=ranked,old_attempts=attempts,nominal_summary=n['summary']))
dump(probe/'FIXED_INPUTS.json',inputs)
(own/'PROTOCOL.md').write_text('''# V832 return-only forward escape development

New explicit user continuation after V830 failed; old V830 and all previous failures/sources/windows remain closed. Root cutoff still2026-11-06 08:00+0800 /1793923200, never extended/reset. One new scientific candidate, no post-freeze interface/scientific repair/retry. No new24 tonight. User wants dynamic outcome then tomorrow matched comparison; comparison is prepared, not automatically started before verified dynamic prerequisites.

Sole change: inside try_handover while executing an existing retained contract, after original16 and original5 forward4 tails ALL reject, append5 original steer values × wheel8/12, each forward escape followed by braking after160 of320 tail ticks. Same actuator ranges/rates, original scoring/minimum .155/self.002/terminal.025/signed forward.02, full8+320 native certificate, actual.15 and all old controls/models/nominal/A*/risk/observation gates. Ordinary admission never enables the new library. Existing tails retain priority. No actual new control without complete original safety certification; forward motion is finite and does not prove renewed viability.

Before global navigation, V831 fixed saved states495 and527 of V83010060002 only, original4216 native exact replay, causal original sensor reconstruction, existing sorted progress>=.02 inputs, at most360400 private native. Original21 candidate trajectories/reasons must match saved old witnesses before appended alternatives. First accepted original-ranked proposal is selected; both fixed states are evaluated, no replacement states. Each selected new complete certificate actual328 plus full repeat must match all qpos/qvel/ctrl/mocap/contact/sensor records<=1e-8 and full native .15/self/ctrl/static gates. Fixed qualification must have at least one successfully executed/repeated escape with positive full goal gain, independent audit, whole-source/decompressedSHA and lossless32MiB archive verification. Otherwise no dependent navigation.

Then5actualt0, fixed10060002 main/success full repeat,10060008 main/repeat, originalNS10010002/WE10010001/EW10010003 each main/repeat, max10 navigation. Original14 auditors plus independent new-library provenance auditor all required. First functional or safety/source/model/truth/state/ctrl/coverage/evidence anomaly stops remaining navigation. All are observed development, no fresh confirmation denominator. Each nav1200public/1200soft1500hard1505outer, t0120/125, full capped subprocess must fit absolute cutoff. All actual model/init/prediction/replay via run_phase singleCPU sequential execution lock.

Same19static entities/single diameter.20 amplitude.25 norm.08actor/3m5%dropout. Truth only physical sensor/offline evaluation; before discovery weaker static reactive contract/public3m prior. Full moving discovery—328 actual stop—new causal reference—actual continuation>=1m—goal<=.45 chain required. Original329execution657planning coverage/full tails/native replay remain. No wider.12axis class/arbitrary occlusion/multiactor/maps/realtime/recursive/RAS guarantee. Training/SAC/realrobot/Stage0, no subagents/chats/messages/network. Local offline campaign gates/stops/audits/archives/restores exactREVIEW_PENDING and closes ledger; preserve original raw and all failures. Deadline after08 only zero-model closure. No unattended new algorithm/seed/pool/comparison if failed.
''')
(probe/'PROTOCOL.md').write_text((own/'PROTOCOL.md').read_text()+'\nV831 is the fixed qualification stage, cap1200s within original morning08. No new global navigation here.\n')
print('PREPARED_RETURN_ONLY_NEW_LIBRARY_AND_FIXED_STATES')
