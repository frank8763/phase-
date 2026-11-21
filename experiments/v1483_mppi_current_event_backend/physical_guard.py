"""Post-native safety checks; evaluator truth never selects commands."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
import route_event
assert Path(route_event.__file__).resolve()==R/'experiments/v1397_event_handoff_integration/route_event.py'


class PhysicalGuard:
    def __init__(self,vehicle,*,setup,current):
        assert vehicle.count==0 and float(vehicle.d.time)==0.
        self.configure(vehicle,setup,current,checked=0)

    @classmethod
    def at_event(cls,vehicle,*,setup,current,canonical_owner):
        assert canonical_owner.vehicle is vehicle and canonical_owner.applied==vehicle.count
        canonical_owner.mode_memory.snapshot(vehicle.count)
        assert canonical_owner.gear.last_tick==vehicle.count-1
        assert len(vehicle.rows)==vehicle.count and len(vehicle.contacts)==vehicle.count+1
        assert vehicle.audit.native_count==vehicle.count and vehicle.bad==0
        instance=cls.__new__(cls)
        instance.configure(vehicle,setup,current,checked=vehicle.count)
        assert current['origin']['native_tick']==vehicle.count and abs(current['origin']['sim_time']-float(vehicle.d.time))<=1e-8
        return instance

    def configure(self,vehicle,setup,current,*,checked):
        assert Path(vehicle.step.__func__.__code__.co_filename).resolve()==R/'experiments/v858_nav2_verified/vehicle.py'
        assert Path(vehicle.check.__func__.__code__.co_filename).resolve()==R/'experiments/v858_nav2_verified/vehicle.py'
        assert Path(vehicle.adapter.compute.__func__.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
        assert abs(vehicle.dt-.01)<=1e-12
        self.current=json.loads(json.dumps(current,allow_nan=False));self.setup=setup;self.checked=checked
        p=Path(__file__).with_name('geometry_binding.py')
        spec=importlib.util.spec_from_file_location('v1415_original_bound_physical_geometry',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.geometry=m.GeometryBinding(current,setup)

    def __call__(self,v):
        import numpy as np
        assert v.count==self.checked+1 and len(v.rows)==v.count and len(v.contacts)==v.count+1
        assert v.audit.native_count==v.count and v.bad==0
        row=v.rows[-1];assert abs(row['time']-float(v.d.time))<=1e-12
        assert row['clearance']>=.15-1e-8 and row['self_margin']>=-1e-10
        assert all(np.array_equal(row[k],getattr(v.d,k)) for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])
        b=list(v.body());enc=v.steering_sample();lat=-float(v.d.qvel[0])*math.sin(b[2])+float(v.d.qvel[1])*math.cos(b[2])
        assert np.isfinite([*b,lat,*enc]).all()
        assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(lat)<=.03,'ACTUAL_BODY_CAP'
        lower=self.geometry.actual(b,v.count)
        assert lower>=.22-1e-8,'ACTUAL_CAUSAL22_VIOLATION'
        self.checked=v.count
        return dict(native=v.count,actual_clearance_m=row['clearance'],actual_self_margin_m=row['self_margin'],causal_lower_m=lower,evaluator_only=True)
