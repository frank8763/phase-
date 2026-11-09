"""Reconstruct each shaping decision from the actual recorded steering/body."""
import gzip
import importlib.util
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v963_independent_shaping',R/'experiments/v961_steering_continuity/independent_shaping.py')
independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
def audit(out):
    out=Path(out);rows=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()))
    setup=json.loads((out/'physics/SETUP.json').read_text())
    with np.load(out/'physics/NATIVE_TRACE.npz')as f:
        q=f['qpos'];v=f['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
        enc=np.c_[q[:,setup['steering_qpos_addresses']],v[:,setup['steering_qvel_addresses']]]
    last=None;commits=0;anchored=0
    for row in rows:
        p=row['packet'];tick=p['native_tick'];assert 0<tick<=len(q)
        assert np.max(abs(np.asarray(p['body'])-body[tick-1]))<=1e-8
        assert np.max(abs(np.r_[p['steering']['position'],p['steering']['velocity']]-enc[tick-1]))<=1e-8
        assert row['nominal_shaping']['raw']==row['raw_wanted']
        independent.check(row['nominal_shaping'],p,last)
        assert row['nominal_shaping']['selected']==row['wanted']
        if row.get('recovery'):
            for a in row['recovery']['alternatives']:
                independent.check(a['shaping'],p,last)
                assert a['shaping']['selected']==a['control']
        s=row['selected_shaping'];next_last=independent.check(s,p,last)
        if row.get('retained_previous'):continue
        assert row['proof']['passed']and s['selected']==[row['proof']['v'],row['proof']['w']]
        assert s['selected'][0]>=0
        last=next_last;commits+=1;anchored+=int(s['mode']=='ANCHORED_TO_MEASURED_STOPPED_STEERING')
    return dict(passed=True,decisions=len(rows),committed_new_certificates=commits,measured_steering_restarts=anchored,
        post_certificate_modifications=0,models=0,integrations=0)
