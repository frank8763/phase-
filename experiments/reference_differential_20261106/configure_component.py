"""Lock the two causal saved states and configure one native qualification."""
from pathlib import Path
import json
import numpy as np
import ast

repo = Path(__file__).resolve().parents[2]
own = repo/'experiments/v838_reference_differential_qualification'
science = repo/'experiments/v839_reference_differential_development'
assert not (own/'INPUT_FREEZE.json').exists()
cell = repo/'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory'
decisions = [json.loads(x) for x in (cell/'control_decisions.jsonl').open()]
states = {x['step']: {k:v for k,v in x.items() if k!='step'} for x in map(json.loads, (cell/'motion_estimate.jsonl').open())}
reference = json.loads((cell/'planning_0306.json').read_text())
entries = []
goal = np.array([4., -2.])
for step, count in [(490, 1), (495, 4)]:
    rows = [x for x in decisions if x['step']==step]
    nominal = next(x for x in rows if x['stage']=='NOMINAL')
    candidates = sorted([x for x in nominal['candidates'] if x['reason']is None], key=lambda x:x['score'], reverse=True)
    old = [x for x in rows if x['stage']=='BACKUP_APPEND']
    eligible = []; seen = set()
    for rank, candidate in enumerate(candidates):
        command = candidate['first_command']; key = tuple(command)
        saved = np.load(cell/'nominal_forecasts'/candidate['nominal_saved_forecast'])
        gain = float(np.linalg.norm(saved['initial_pose'][:2]-goal)-np.linalg.norm(saved['poses'][-1,:2]-goal))
        matches = [x for x in old if np.array_equal(x['first_command'],command)]
        if key in seen or gain < .02 or not matches:
            continue
        seen.add(key)
        eligible.append(dict(rank=rank, command=command, nominal_progress_m=gain, old=matches[0]))
        if len(eligible)==count:
            break
    assert len(eligible)==count
    positions = np.asarray(reference['path'])
    q = saved['initial_pose'] if step==495 else np.asarray(json.loads((cell/'planning_0531.json').read_text())['pose'])
    # The exact reference index is recomputed at the real saved snapshot in probe.
    entries.append(dict(step=step, state=states[step], eligible=eligible,
        reference=dict(path=reference['path'], index=None, goal_xy=goal.tolist(), wheel_base=.60),
        reference_source='runs/v830_ranked_return_development/main_slot01/paired/geometry_memory/planning_0306.json'))
(own/'FIXED_INPUTS.json').write_text(json.dumps(entries,indent=2)+'\n')
p=own/'helpers.py';s=p.read_text();start=s.index('def eligible(')
s=s[:start]+"def eligible(entry,goal):\n assert np.array_equal(goal,[4.,-2.])\n return entry['eligible']\n";p.write_text(s)
p=own/'probe.py';s=p.read_text()
s=s.replace('1000000','500000').replace('>527','>495').replace('528','496').replace('[495,527]','[490,495]').replace('4216','3960').replace('OLD_4216','OLD_3960')
s=s.replace("samples.append(dict(qpos=data.qpos.copy(),qvel=data.qvel.copy()))", "\n  if len(samples)<8:samples.append(dict(qpos=data.qpos.copy(),qvel=data.qvel.copy()))")
s=s.replace("reserved.allow_forward_escape=True;reserved.escape_goal_xy=np.asarray(protocol['goal_xy']);cursor=[0];maximum=[0.]", "reserved.public_goal_xy=np.asarray(protocol['goal_xy']);reference=np.asarray(entry['reference']['path']);index=int(np.argmin(np.linalg.norm(reference[:,:2]-d.qpos[:2],axis=1)));reserved.set_reference(reference,min(index,len(reference)-2),protocol['goal_xy'],.60);cursor=[0];maximum=[0.]")
s=s.replace("if j<21:", "if j<len(proposal['old']['detail']['candidates']):")
s=s.replace("old_candidate=proposal['old']['detail']['candidates'][j];old=np.load(cell/old_candidate['early_rejection_witness_file'])['poses'];complete=np.vstack([poses(np.asarray([x['qpos']for x in samples])),trajectory]);error=float(np.max(abs(complete-old)));maximum[0]=max(maximum[0],error);assert error<=1e-8,'ORIGINAL21_NATIVE_FORECAST_CHANGED'", "old_candidate=proposal['old']['detail']['candidates'][j]\n     if old_candidate['early_rejection_witness_file']is not None:\n      old=np.load(cell/old_candidate['early_rejection_witness_file'])['poses'];complete=np.vstack([poses(np.asarray([x['qpos']for x in samples])),trajectory]);error=float(np.max(abs(complete-old)));maximum[0]=max(maximum[0],error);assert error<=1e-8,'ORIGINAL21_NATIVE_FORECAST_CHANGED'")
s=s.replace("assert len(detail['candidates'])==166", "assert len(detail['candidates'])in[1,16,21,39]")
s=s.replace("assert a['reason']==b['reason']=='TIME_CLEARANCE'and a['library']==b['library']and a['target_command']==b['target_command']", "assert a['library']==b['library']and a['target_command']==b['target_command']\n    if b['reason']=='TIME_CLEARANCE':assert a['reason']=='TIME_CLEARANCE'")
s=s.replace("assert abs(a['early_rejection_witness_value_m']-b['early_rejection_witness_value_m'])<=1e-8", "if b['early_rejection_witness_value_m']is not None:assert abs(a['early_rejection_witness_value_m']-b['early_rejection_witness_value_m'])<=1e-8")
s=s.replace("if summary is not None:\n    assert summary['recovery_kind']=='FORWARD_TIMED_ESCAPE_BRAKE';selected=(proposal,reserved);break", "if summary is not None and summary['recovery_kind']=='REFERENCE_FOLLOW_BRAKE':\n    selected=(proposal,reserved);break")
s=s.replace("cache['qpos']]);v=np.vstack([[x['qvel']for x in samples],cache['qvel']]);controls=np.vstack([np.repeat([proposal['command']],8,axis=0),cache['controls']])", "cache['qpos'],cache['one_cycle_continuation']['extra_qpos']]);v=np.vstack([[x['qvel']for x in samples],cache['qvel'],cache['one_cycle_continuation']['extra_qvel']]);controls=np.vstack([np.repeat([proposal['command']],8,axis=0),cache['controls'],cache['one_cycle_continuation']['extra_controls']])")
s=s.replace("assert len(q)==328", "assert len(q)==336")
s=s.replace("qualified=gain>0", "qualified=gain>=.02")
s=s.replace("complete_goal_progress_m=gain,minimum_causal_clearance_m", "complete_goal_progress_m=gain,minimum_causal_clearance_m")
p.write_text(s)
p=science/'reserved_recovery.py';s=p.read_text().replace("'initial_qpos':initial_q.copy(),'initial_qvel'", "'prefix_initial_qpos':real.qpos.copy(),'initial_qpos':initial_q.copy(),'initial_qvel'")
anchor="                if following:detail.update(lookahead_m=lookahead,wheel_speed=wheel)"
replacement="""                if following:detail.update(lookahead_m=lookahead,wheel_speed=wheel)
                if active and (following or not proof['rejected']or os.environ.get('PHASE_SAVE_ALL_REFERENCE_CANDIDATES')=='1'):
                    folder=self.cell/'full_predictions';folder.mkdir(exist_ok=True);saved=folder/f'prediction_{next(_witness_counter):07d}.npz'
                    assert not saved.exists();np.savez_compressed(saved,poses=np.vstack((prefix,extended['poses'])),controls=np.vstack((np.repeat([proposal],8,axis=0),extended['controls'])),self_bounds=extended['self_bounds'])
                    detail['full_forecast_file']=str(saved.relative_to(self.cell))
"""
s=s.replace('import gzip,json,math,itertools,time,hashlib','import gzip,json,math,itertools,time,hashlib,os').replace(anchor,replacement.rstrip())
p.write_text(s)
p=science/'reference_certificate_audit.py';s=p.read_text().replace("np.asarray(c['initial_qpos'])[:2]-goal", "np.asarray(c['prefix_initial_qpos'])[:2]-goal");p.write_text(s)
for path in own.glob('*.py'):
    ast.parse(path.read_text(),filename=str(path))
for path in science.glob('*.py'):
    ast.parse(path.read_text(),filename=str(path))
print('TWO_FIXED_INPUTS_LOCKED_490_AND_495_MAX_FIVE_PREFIX_COMMANDS')
