"""Existing actual/source/control gates under the current model's fixed field."""
import copy
from pathlib import Path
import math
R=Path(__file__).resolve().parents[2]


class PhysicalGuard:
    def __init__(self,*,vehicle,native,method,geometry):
        assert native.vehicle is vehicle and native.applied==vehicle.count
        assert native.gear.last_tick==vehicle.count-1
        assert native.mode_memory.snapshot(vehicle.count)==method['base_method']['physical_source']['mode_history']
        assert method['base_method']['fixed_origin_native']==vehicle.count
        assert Path(vehicle.step.__func__.__code__.co_filename).resolve()==R/'experiments/v858_nav2_verified/vehicle.py'
        assert Path(vehicle.check.__func__.__code__.co_filename).resolve()==R/'experiments/v858_nav2_verified/vehicle.py'
        assert Path(vehicle.adapter.compute.__func__.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
        assert abs(vehicle.dt-.01)<=1e-12
        self.checked=vehicle.count;self.method=copy.deepcopy(method);self.geometry=geometry

    def __call__(self,vehicle):
        import numpy as np
        v=vehicle
        assert v.count==self.checked+1 and len(v.rows)==v.count and len(v.contacts)==v.count+1
        assert v.audit.native_count==v.count and v.bad==0
        row=v.rows[-1]
        assert abs(row['time']-float(v.d.time))<=1e-12
        assert row['clearance']>=.15-1e-8 and row['self_margin']>=-1e-10
        assert all(np.array_equal(row[k],getattr(v.d,k))for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'))
        body=list(v.body());enc=v.steering_sample()
        lateral=-float(v.d.qvel[0])*math.sin(body[2])+float(v.d.qvel[1])*math.cos(body[2])
        assert np.isfinite([*body,lateral,*enc]).all()
        assert abs(body[3])<=.13 and abs(body[4])<=.16 and abs(lateral)<=.03
        lower=float(self.geometry.actual(body,v.count))
        assert lower>=.22-1e-8,'ACTUAL_CURRENT_CAUSAL22_VIOLATION'
        self.checked=v.count
        return dict(native=v.count,actual_clearance_m=row['clearance'],actual_self_margin_m=row['self_margin'],
            causal_lower_m=lower,response_method_sha256=self.method['response_method_sha256'],evaluator_only=True)
