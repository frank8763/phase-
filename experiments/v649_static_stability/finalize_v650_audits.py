"""Sequential post-window physics replay and read-only integrity audit.
Replays consume the SAME V650 wall-clock window. No automatic static acceptance.
"""
import json,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v650_static_acceptance';window=root/'acceptance_window02';origin=json.loads((root/'BUDGET_ORIGIN.json').read_text());deadline=origin['absolute_deadline_unix'];completion=json.loads((window/'COMPLETION.json').read_text());rows=json.loads((window/'CONFIRMATION_RESULTS.json').read_text())if(window/'CONFIRMATION_RESULTS.json').exists()else[]
assert completion['status']!='CONFIRMATION_RUNNING'
selected=[x['name']for x in rows if x['result']is not None]
for p in sorted(root.glob('repeat_*/paired/completion.json')):
 if json.loads(p.read_text()).get('results'):selected.append(p.parent.parent.name)
records=[]
for name in selected:
 if deadline-time.time()<40:break
 pair=root/name/'paired';begin=time.monotonic();audit=subprocess.run([str(repo/'run_phase.sh'),'experiments/v650_static_acceptance/replay_native_audit.py',str(pair)],cwd=repo,text=True,capture_output=True,timeout=35)
 (pair/'native_replay.console').write_text(audit.stdout+audit.stderr);p=pair/'NATIVE_REPLAY_AUDIT.json';replay=json.loads(p.read_text())if p.exists()else None
 integrity=subprocess.run(['python',str(repo/'experiments/v648_static_unknown/audit_results.py'),str(pair)],cwd=repo,text=True,capture_output=True,timeout=15)
 (pair/'INTEGRITY_AUDIT.console').write_text(integrity.stdout+integrity.stderr)
 row={'name':name,'wall_s':time.monotonic()-begin,'integrity_passed':integrity.returncode==0,'replay':replay};records.append(row);(root/'FINAL_PHYSICAL_AUDITS.json').write_text(json.dumps(records,indent=2))
 print(name,'integrity',row['integrity_passed'],'replay',None if replay is None else replay['status'],flush=True)
print('Completed physical audits',len(records),'of',len(selected),'remaining window seconds',deadline-time.time(),flush=True)
