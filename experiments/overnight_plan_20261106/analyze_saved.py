"""Read completed V843 evidence only; never import models or launch work."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / 'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'
OUT = REPO / 'runs/overnight_plan_20261106/SAVED_V843_ANALYSIS.json'


def read(name):
    return json.loads((RAW / name).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assert-arrival', action='store_true')
    args = parser.parse_args()
    result = read('result.json')
    trace = read('trace.json')
    distances = [float(row['goal_distance_m']) for row in trace]
    negative = {row['step'] for row in trace if sum(row['applied_ctrl'][2:4]) < 0}
    plans = []
    for path in sorted(RAW.glob('planning_*.json')):
        row = json.loads(path.read_text())
        stats = row['stats']
        policy = stats.get('spatial_soft_reference', {})
        plans.append(dict(step=row['step'], status=stats['status'],
                          expanded=stats['expanded'], wall_s=stats['wall_s'],
                          forward_reference_selected=policy.get('forward_reference_selected'),
                          bidirectional_called=policy.get('original_bidirectional_fallback_called')))
    joint = collections.Counter()
    with (RAW / 'early_joint_decisions.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            joint['events'] += 1
            if row['selected_rank'] is None:
                joint['none_selected'] += 1
                continue
            step = row['step']
            before = math.dist(row['real_qpos'][:2], row['public_goal_xy'])
            joint['selected'] += 1
            joint['first_public_goal_worsened'] += before < distances[step]
            if step + 40 < len(distances):
                joint['with_40_public_followup'] += 1
                joint['40_public_goal_worsened'] += before < distances[step + 40]
    negative_roles = collections.Counter()
    with (RAW / 'model_admission.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['step'] in negative:
                negative_roles[row['status']] += 1
    source_files = [RAW / name for name in ['result.json', 'trace.json',
                    'early_joint_decisions.jsonl', 'model_admission.jsonl']]
    source_files += sorted(RAW.glob('planning_*.json'))
    sources = []
    for path in source_files:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        sources.append(dict(path=str(path.relative_to(REPO)), bytes=path.stat().st_size,
                            sha256=digest.hexdigest()))
    summary = dict(
        scope='SAVED_EVIDENCE_ONLY_NOT_A_CONTROLLER_OR_NEW_EXPERIMENT',
        new_models=0, new_integrations=0, new_predictions=0,
        old_outcome=result['outcome'], strict_arrival=result['strict_safe_arrival'],
        final_goal_distance_m=distances[-1], best_goal_distance_m=min(distances),
        best_public_step=distances.index(min(distances)),
        actual_path_length_m=sum(math.dist(a['pose'][:2], b['pose'][:2])
                                 for a, b in zip(trace, trace[1:])),
        reverse_reference_public_steps=sum((row.get('active_gear') or 0) < 0 for row in trace),
        negative_mean_wheel_command_public_steps=len(negative),
        negative_command_roles=dict(negative_roles),
        navigation_wall_s=result['elapsed_s'], global_planning_wall_s=result['planning_wall_s'],
        global_planning_wall_fraction=result['planning_wall_s'] / result['elapsed_s'],
        navigation_native=result['physics_steps'], private_native=result['prediction_steps'],
        global_reference_status_counts=dict(collections.Counter(row['status'] for row in plans)),
        search_16000_budget_hits=sum(row['expanded'] >= 16000 for row in plans),
        early_joint=dict(joint), plans=plans, sources=sources,
        interpretation_limits=[
            'Wheel command sign is not a measurement of actual signed displacement.',
            'Forty-step followup includes intervening decisions; it is not a prediction replay error.',
            'No counterfactual bidirectional search has been performed on forward-prefix states.',
            'The share of remaining wall time due to prediction, geometry, compression and I/O is unmeasured.',
            'A failed arrival does not authorize changing the frozen V843 batch.'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ['sources', 'plans', 'interpretation_limits']}, ensure_ascii=False))
    if args.assert_arrival:
        assert result['outcome'] == 'GOAL' and result['strict_safe_arrival'] and distances[-1] <= .45, \
            f"SAVED_ARRIVAL_FAILURE: {result['outcome']}, goal distance={distances[-1]:.9f}m"


if __name__ == '__main__':
    main()
