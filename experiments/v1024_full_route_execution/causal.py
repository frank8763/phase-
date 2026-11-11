"""Packet-only sensor evidence and original finite braking permissions."""
import importlib.util,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v1023_dense_input_route'),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v889_motion_envelope_software')]
from geometry_model import ref,REQUIRED,RHO
from whole_input import Predictor,PARAMETERS,initial
from support_envelope import SupportEnvelope
ps=importlib.util.spec_from_file_location('v1024_original_periodic_evidence',R/'experiments/v1020_terminal_two_route_development/periodic_support.py');pm=importlib.util.module_from_spec(ps);ps.loader.exec_module(pm);PeriodicSupport=pm.PeriodicSupport
s=importlib.util.spec_from_file_location('v1024_exact_sensor_math',R/'experiments/v887_exact_lidar_software/exact_lidar.py');lidar=importlib.util.module_from_spec(s);s.loader.exec_module(lidar)
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
class Evidence:
    def __init__(self,known):
        self.known=known;self.envelope=SupportEnvelope(known,lidar.get_lidar_features);self.periodic=PeriodicSupport();self.first=None;self.snapshots=[];self.last_scan=None
    def update(self,scan):
        # Whitelist deliberately excludes physical raw rays, evaluator labels,
        # actual actor position, phase, axis or future geometry.
        scan={k:scan[k]for k in ['native_tick','time','xy','yaw','ranges']}
        self.last_scan=scan;row=self.envelope.update(scan)
        self.periodic.update(scan['time'],scan['native_tick'],row['support_bounds'])
        if row['information_mode']=='TRACKED'and self.first is None:self.first=scan.copy()
        self.snapshots.append(row);return self.first is not None
    def source(self,vehicle):
        assert self.first is not None and self.last_scan is not None,'NO_CAUSAL_DISCOVERY'
        scan=self.last_scan
        return dict(source_native_tick=scan['native_tick'],source_age_s=float(vehicle.d.time)-scan['time'],decision_at=time.monotonic(),periodic=self.periodic.snapshot())

def packet(vehicle,discovered):
    now=time.monotonic();enc=vehicle.steering_sample()
    return dict(body=list(vehicle.body()),native_tick=vehicle.count,sim_time=float(vehicle.d.time),body_measured_at=now,sent_at=now,dynamic_discovered=bool(discovered),
        steering=dict(position=enc[:2].tolist(),velocity=enc[2:].tolist(),native_tick=vehicle.count,measured_at=now),
        controller_memory=dict(last_ctrl=vehicle.adapter.last.tolist(),integral=float(vehicle.adapter.integral)))

def brake(setup,p,evidence):
    engine=Predictor(setup,initial(p),PARAMETERS);states=[engine.state.copy()];controls=[]
    for _ in range(200):
        ss,u=engine.step(0.,0.,False);states.append(ss);controls.append(u)
    states=np.asarray(states);controls=np.asarray(controls);a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);minimum=float(a.min())
    if evidence.first is not None:
        age=p['sim_time']-evidence.envelope.when;assert 0<=age<=.051,'BRAKE_SOURCE_STALE'
        bounds=evidence.envelope.support[None,:]+.08*(age+np.arange(201)[:,None]*.01+.05)
        poses=states[:,:3];c=np.cos(poses[:,2]);s=np.sin(poses[:,2]);front=np.c_[c,s];left=np.c_[-s,c]
        low=poses[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T)
        minimum=min(minimum,float((low-bounds-.1).max(axis=1).min()))
    assert minimum>=REQUIRED,'NO_COMPLETE_CAUSAL_BRAKE_PERMISSION'
    assert abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03,'BRAKE_PREDICTION_NOT_STOPPED'
    return dict(passed=True,scope='FINITE_ORIGINAL_200_STOP_PERMISSION',state_path=states.tolist(),planned_body_requests=[[0.,0.,False]]*200,predicted_actuator_controls=controls.tolist(),
        minimum_raw_clearance_m=minimum,required_raw_m=REQUIRED,source_native_tick=None if evidence.last_scan is None else evidence.last_scan['native_tick'],models=0,integrations=0)
