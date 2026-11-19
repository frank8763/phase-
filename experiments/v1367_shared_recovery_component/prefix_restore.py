"""Reproduce original prefix by native integration only; never write root/time."""
import json
from pathlib import Path
import time
import numpy as np


def restore(vehicle,task,step,deadline):
    prior=Path(task['prior_raw']);rows=json.loads((prior/'APPLIED_JOURNAL.json').read_text())
    target=task['origin_native_tick'];maximum=memory=0.
    original_setup=json.loads((prior/'physics/SETUP.json').read_text())
    current_setup=json.loads((vehicle.out/'SETUP.json').read_text())
    assert current_setup['model_sha256']==original_setup['model_sha256'],'PREFIX_MODEL_NOT_ORIGINAL'
    vehicle.scan()
    with np.load(prior/'physics/NATIVE_TRACE.npz') as trace:
        # NPZ members are decompressed on every lookup. Read each required
        # prefix once before the per-native comparison, preserving every tick.
        reference={key:trace[key][:target].copy() for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        for index,row in enumerate(rows[:target]):
            assert time.time()<deadline-180,'PREFIX_ROOT_DEADLINE'
            assert vehicle.count==index and row['before_native']==index and row['applied']
            memory=max(memory,float(np.max(abs(vehicle.adapter.last-row['last_ctrl']))),abs(vehicle.adapter.integral-row['integral']))
            assert memory<=1e-8,'PREFIX_CONTROL_MEMORY_MISMATCH'
            step(*row['upstream_request'][:2],'HISTORICAL_PREFIX')
            for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                actual=np.asarray(getattr(vehicle.d,key));expected=reference[key][index]
                if actual.size:maximum=max(maximum,float(abs(actual-expected).max()))
            assert maximum<=1e-8,'PREFIX_FULL_STATE_OR_CONTROL_MISMATCH'
            if vehicle.count%5==0:vehicle.scan()
    assert vehicle.count==target and abs(vehicle.d.time-task['origin_sim_time'])<=1e-7
    assert np.max(abs(np.asarray(vehicle.body())-task['origin_body']))<=1e-8
    next_row=rows[target]
    memory=max(memory,float(np.max(abs(vehicle.adapter.last-next_row['last_ctrl']))),abs(vehicle.adapter.integral-next_row['integral']))
    assert memory<=1e-8,'PREFIX_FINAL_CONTROL_MEMORY_MISMATCH'
    return dict(passed=True,historical_prefix_replay_native=target,full_state_ctrl_mocap_error=maximum,
        control_memory_error=memory,no_root_state_or_clock_rewrite=True,exact_original_model_SHA=True,
        actual_origin_native=vehicle.count,actual_origin_sim_time=float(vehicle.d.time))
