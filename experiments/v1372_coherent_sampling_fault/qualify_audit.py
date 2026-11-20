"""Independent audit seam against real saved sensor/body records and mutations."""
import copy
import gzip
import importlib.abc
import sys
from component_context import *
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('AUDIT_QUALIFICATION_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from sampling_audit import frame_audit,state_body_audit
import numpy as np

def main():
    prior=Path(read(C/'TASKS.json')[0]['prior_raw']);journal=read(prior/'APPLIED_JOURNAL.json')
    with gzip.open(prior/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    wires=[]
    for index,tick in enumerate([41390,41415]):
        s=next(x for x in sensors if x['native_tick']==tick)
        wires.append(dict(sequence=index,native_tick=tick,sim_time=s['time'],body=journal[tick]['body'],ranges_m=s['ranges'],sampled_at=10.+index,
            sensor_frame=dict(native_tick=tick,time=s['time'],xy=s['xy'],yaw=s['yaw'],sampled_at=10.+index)))
    assert frame_audit(wires,sensors,journal,41390)
    negative=[]
    for name in ['missing_actual_scan','forged_acquisition','changed_body','changed_range','old_sensor_tick','nonmonotonic_age']:
        w=copy.deepcopy(wires);ss=sensors
        if name=='missing_actual_scan':ss=[s for s in sensors if s['native_tick']!=41415]
        if name=='forged_acquisition':w[-1]['sampled_at']+=.1
        if name=='changed_body':w[-1]['body'][0]+=.01
        if name=='changed_range':w[-1]['ranges_m'][0]+=.01
        if name=='old_sensor_tick':w[-1]['sensor_frame']['native_tick']=41390
        if name=='nonmonotonic_age':w[-1]['sampled_at']=w[-1]['sensor_frame']['sampled_at']=9.
        try:frame_audit(w,ss,journal,41390)
        except (AssertionError,KeyError):negative.append(name)
        else:raise AssertionError('AUDIT_ACCEPTED_TAMPER '+name)
    assert not any(s['native_tick']==41410 for s in sensors),'OLD_MISSING_SENSOR_CHANGED'
    with np.load(prior/'physics/NATIVE_TRACE.npz') as z:
        # All recorded body feedback, not a selected checkpoint only.
        trace={k:z[k] for k in ['qpos','qvel']}
    maximum=state_body_audit(trace,journal,read(prior/'INITIAL_PACKET.json')['body'])
    changed=copy.deepcopy(journal[-2:]);mini={k:v[-2:-1] for k,v in trace.items()}
    state_body_audit(mini,changed,journal[-2]['body'])
    changed[-1]['body'][3]+=.001
    try:state_body_audit(mini,changed,journal[-2]['body'])
    except AssertionError:negative.append('body_velocity_vs_actual_state')
    else:raise AssertionError('BODY_VELOCITY_TAMPER_ACCEPTED')
    assert sources();dump(O/'AUDIT_QUALIFICATION.json',dict(passed=True,real_saved_sensor_ticks=[41390,41415],negative_cases=negative,
        full_saved_body_records=len(journal),maximum_body_state_error=maximum,absent_original41410_still_absent=True,models=0,physical_native=0,tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
    print(json.dumps(dict(passed=True,negative_cases=len(negative),models=0)))
if __name__=='__main__':main()
