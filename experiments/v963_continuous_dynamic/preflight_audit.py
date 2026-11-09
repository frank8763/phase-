"""Saved actual t0 contracts and source bytes only, no model import."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
def audit(tasks):
    rows=[]
    for task in tasks:
        p=Path(task['preflight_output']);a=json.loads((p/'PREFLIGHT.json').read_text());s=json.loads((p/'SETUP.json').read_text())
        native=json.loads((p/'MODEL_BUILD_CONTRACT.json').read_text());scan=a['scan'];contacts=json.loads(gzip.decompress((p/'CONTACTS.json.gz').read_bytes()))
        with np.load(p/'INITIAL_STATE.npz')as f:assert all(np.isfinite(f[k]).all()for k in f.files)
        assert a['passed']and a['actual_native']==a['replay_native']==a['private_native']==0
        assert a['summary']['root_guard_native_count']==0 and a['summary']['fully_recorded_native']==0
        assert a['summary']['first_actor_detection']is None and a['summary']['bad_contacts']==0 and a['summary']['minimum_actual_clearance_m']>=.15
        assert scan['native_tick']==0 and scan['time']==0. and len(scan['ranges'])==32
        assert not any(x[2]in{'robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'}for frame in contacts for x in frame)
        assert native['interface']['passed']and s['dynamic']and s['seed']==task['seed']and s['case']['id']==task['case_id']
        assert s['actor']['phase_rad']==task['phase']and s['actor']['maximum_speed_m_s']==.08
        assert hashlib.sha256((p/'scene_model.mjb').read_bytes()).hexdigest()==s['model_sha256']
        rows.append(dict(task_id=task['task_id'],passed=True,actual_native=0,replay_native=0,models_initialized=1))
    return dict(passed=len(rows)==len(tasks)>0,rows=rows,models_initialized=len(rows),actual_native=0,replay_native=0,private_native=0,models_during_audit=0)
