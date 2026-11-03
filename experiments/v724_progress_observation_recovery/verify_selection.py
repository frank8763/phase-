"""Zero-integration calibration against all safe native V723 diagnostic tails."""
import json,math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from observation_selection import choose_backup
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v724_recovery_selection_calibration';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text())
pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');states={x['step']:x for x in map(json.loads,(pair/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())};rows=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];records=read(repo/'runs/v723_recovery_observability_probe/CANDIDATES.json');field=SimpleNamespace(rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']));details=[]
for step in[92,133]:
    selected=[x for x in records if x['checkpoint']==step and x['admissible']and x['kind']in['BRAKE_ONLY','REVERSE_BRAKE']];candidates=[]
    for x in selected:
        data=np.load(repo/'runs/v723_recovery_observability_probe'/('CHECKPOINT_%03d_CANDIDATE_%02d.npz'%(step,x['index'])))
        candidates.append(dict(poses=data['poses'][8:],target=np.asarray(x['target_command']),recovery_kind=x['kind'],minimum_causal_predicted_clearance_m=x['minimum_causal_clearance_m'],original_index=x['index']))
    current=np.asarray(rows[step-1]['qpos_full'])[:2];answer,metadata=choose_backup(candidates,current,np.asarray(p['goal_xy']),field,states[step]);repeat,second=choose_backup(candidates,current,np.asarray(p['goal_xy']),field,states[step]);checks=[]
    for row in metadata['candidates']:
        original=selected[row['safe_index']]
        checks.append(abs(original['goal_progress_m']-row['goal_progress_m'])<=1e-12)
        if row['within_best_progress_band']:checks.append(row['potential_visible_cells']==original['visibility_heuristic']['potential_unknown_visible_cells'])
    expected=18 if step==92 else 23
    checks.extend([answer['original_index']==expected,metadata==second,answer is repeat,metadata['safety_uses_future_measurement']is False])
    details.append(dict(step=step,checks_passed=all(checks),chosen_original_candidate_index=answer['original_index'],metadata=metadata))
out=dict(status='FIXED_RECOVERY_RANKING_AND_GEOMETRIC_VISIBILITY_VALIDATED'if all(x['checks_passed']for x in details)else'FAIL',details=details,new_initializations=0,new_integrations=0,training_updates=0)
(root/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['status']!='FAIL'
