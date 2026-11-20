"""Exact actual32600 prefix including original parked steering mode memory."""
import json
import time
from pathlib import Path
import numpy as np
def restore(vehicle,task,step,deadline):
    prior=Path(task['prior_raw']);rows=json.loads((prior/'APPLIED_JOURNAL.json').read_text());target=32600
    final=json.loads((prior/'FINAL_PACKET.json').read_text());assert len(rows)==target
    setup=json.loads((prior/'physics/SETUP.json').read_text());new=json.loads((vehicle.out/'SETUP.json').read_text());assert setup['model_sha256']==new['model_sha256']
    with np.load(prior/'physics/NATIVE_TRACE.npz') as z:reference={k:z[k].copy() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    maximum=memory=0.;vehicle.scan()
    for i,row in enumerate(rows):
        assert time.time()<deadline-180 and vehicle.count==row['before_native']==i and row['applied']
        memory=max(memory,float(abs(vehicle.adapter.last-row['last_ctrl']).max()),abs(vehicle.adapter.integral-row['integral']))
        assert memory<=1e-8 and bool(getattr(vehicle.adapter,'_steering_motion_active',False))==row.get('steering_motion_active_before',False)
        vehicle.adapter.parked_target=row.get('parked_target')
        step(*row['upstream_request'][:2],'HISTORICAL_PREFIX')
        for key in reference:
            actual=np.asarray(getattr(vehicle.d,key));expected=reference[key][i]
            if actual.size:maximum=max(maximum,float(abs(actual-expected).max()))
        assert maximum<=1e-8,'PREFIX_FULL_STATE_CTRL_MOCAP_MISMATCH'
        if vehicle.count%5==0:vehicle.scan()
    assert vehicle.count==32600 and abs(vehicle.d.time-326.)<=1e-7
    assert abs(np.asarray(vehicle.body())-np.asarray(final['body'])).max()<=1e-8
    assert abs(vehicle.adapter.last-final['controller_memory']['last_ctrl']).max()<=1e-8
    assert abs(vehicle.adapter.integral-final['controller_memory']['integral'])<=1e-8
    vehicle.adapter.parked_target=None
    return dict(passed=True,historical_prefix_replay_native=target,full_state_ctrl_mocap_error=maximum,control_memory_error=memory,no_root_state_or_clock_rewrite=True,exact_original_model_SHA=True)
