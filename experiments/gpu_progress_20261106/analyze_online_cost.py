"""Saved-only online-cost decomposition and exact full-control duplicate witness."""
import hashlib
import json
from pathlib import Path

import numpy as np

REPO=Path(__file__).resolve().parents[2]
CELL=REPO/'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'
OUT=REPO/'runs/gpu_online_cost_20261106'
STEPS={374,683,893,1198}


def schedule(target,last,limits,rate):
    rows=[]
    command=np.asarray(last,float).copy()
    for tick in range(0,240,8):
        active=np.asarray(target,float).copy()
        if tick>=80:active[2:]=0.
        command=np.clip(np.clip(active,limits[:,0],limits[:,1]),command-rate,command+rate)
        rows.extend([command.copy()]*8)
    return np.asarray(rows)


def main():
    OUT.mkdir(exist_ok=True)
    result=json.loads((CELL/'result.json').read_text())
    trace=json.loads((CELL/'trace.json').read_text())
    contract=json.loads((CELL/'ACTUATOR_COMMAND_CONTRACT.json').read_text())
    limits,rate=np.asarray(contract['limits']),np.asarray(contract['rate'])
    records=[]
    with(CELL/'control_decisions.jsonl').open()as stream:
        for line in stream:
            row=json.loads(line)
            if row.get('step')not in STEPS or row.get('stage')!='NOMINAL':continue
            last=trace[row['step']-1]['applied_ctrl'][:4]
            full_groups={};first_groups={};maximum=0.
            for index,candidate in enumerate(row['candidates']):
                controls=schedule(candidate['target_command'],last,limits,rate)
                source=CELL/'nominal_forecasts'/candidate['nominal_saved_forecast']
                with np.load(source)as saved:
                    error=float(np.max(abs(controls-saved['controls'])))
                    assert error<=1e-12,'SAVED_FULL_CONTROL_RECONSTRUCTION_MISMATCH'
                    maximum=max(maximum,error)
                    # Exact byte equality, never first-command-only equivalence.
                    key=hashlib.sha256(controls.tobytes()).hexdigest()
                    entry=full_groups.get(key)
                    if entry is None:full_groups[key]=dict(indices=[index],poses=saved['poses'].copy())
                    else:
                        assert np.max(abs(entry['poses']-saved['poses']))<=1e-8
                        entry['indices'].append(index)
                    first_groups.setdefault(controls[0].tobytes(),[]).append(key)
            records.append(dict(step=row['step'],nominal_candidates=len(row['candidates']),
                distinct_complete_schedules=len(full_groups),exact_duplicate_schedules=len(row['candidates'])-len(full_groups),
                distinct_first_commands=len(first_groups),
                first_command_groups_with_different_futures=sum(len(set(v))>1 for v in first_groups.values()),
                duplicate_groups=[v['indices']for v in full_groups.values()if len(v['indices'])>1],
                maximum_control_reconstruction_error=maximum))
    assert len(records)==4
    payload=dict(scope='SAVED_ONLY_NO_MODEL_OR_ALGORITHM_CHANGE',new_models=0,new_integrations=0,
        navigation_wall_s=result['elapsed_s'],simulation_time_s=result['physics_steps']*.01,
        mean_online_cycle_s=result['elapsed_s']/result['public_steps'],
        global_search_wall_s=result['planning_wall_s'],
        online_time_not_split_further_s=result['elapsed_s']-result['planning_wall_s'],
        private_native=result['prediction_steps'],records=records,
        exact_duplicate_fraction=sum(v['exact_duplicate_schedules']for v in records)/sum(v['nominal_candidates']for v in records),
        full_control_hash_cache_not_yet_implemented=True,
        first_command_only_deduplication_invalid=True)
    (OUT/'ANALYSIS.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload),flush=True)


if __name__=='__main__':main()
