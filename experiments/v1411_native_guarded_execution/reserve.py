"""Current measured packet -> original full200 zero branch; no launch rights."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import sys

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
import route_event
assert Path(route_event.__file__).resolve()==R/'experiments/v1397_event_handoff_integration/route_event.py'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class CurrentReserve:
    def __init__(self,*,setup,causal_snapshot,authority,lock,accounting):
        self.setup=copy.deepcopy(setup);self.snapshot=copy.deepcopy(causal_snapshot)
        self.authority=copy.deepcopy(authority);self.lock=lock;self.accounting=accounting
        self.snapshot_sha256=digest(self.snapshot)

    def __call__(self,packet,modes):
        a=self.authority;c=self.accounting
        parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
        assert a['scope']=='CURRENT_ACTUAL_RESERVE' and a['physical_authorized'] is True
        assert a['round_id']==parent['active_round'] and parent['models_now_authorized']
        assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
        assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()==parent['boot_id']
        assert a['absolute_deadline_unix']<=1795395600 and a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        assert Path('/proc/self/fd/'+str(self.lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert a['tested_source_hashes'] and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in a['tested_source_hashes'].items())
        assert digest(self.snapshot)==self.snapshot_sha256==a['causal_snapshot_sha256']
        assert modes['covered_native']==packet['native_tick']
        assert all(packet[k]==modes[k] for k in ['coupled_episode','steering_motion_active','parked_target'])
        assert not c.get('analytical_inflight_unknown',False) and not c.get('construction_inflight_unknown',False)
        assert c['analytical_native']+200<=a['maximum_analytical_native']
        assert c['predictor_constructions']<a['maximum_predictor_constructions']
        source=exact('v1411_original_scalar_generator',R/'experiments/v1410_scalar_feedback_witness/generator.py')
        field=exact('v1411_current_coefficient_enclosure',R/'experiments/v1397_event_handoff_integration/causal_bridge_field.py')
        forecast=field.all_future(self.snapshot,current_native=packet['native_tick'],current_sim_time=packet['sim_time'])
        Predictor,initial,kernel,Adapter,Geometry,_,_=source.binding()
        import numpy as np
        before=digest(packet)
        c['construction_inflight_unknown']=True
        p=Predictor(self.setup,initial(packet),kernel.PARAMETERS)
        c['predictor_constructions']+=1;c['construction_inflight_unknown']=False
        assert p.adapter.__class__ is Adapter
        p.adapter.parked_target=None
        # Closing the parked target is the prospective zero branch only;
        # coupled_episode remains the actual canonical-t0 tracked episode.
        p.adapter._steering_motion_active=packet['steering_motion_active']
        assert p.coupled_episode==packet['coupled_episode']
        assert np.array_equal(source.feedback.current(p),[*packet['steering']['position'],*packet['steering']['velocity']])
        geometry=Geometry(self.setup['known'],[*forecast['center'],forecast['radius_m']])
        states=[p.state.copy()];controls=[]
        for _ in range(200):
            assert time.time()<a['absolute_deadline_unix']-30 and time.monotonic()<a['hard_stop_monotonic']-30
            c['analytical_inflight_unknown']=True;s,u=p.step(0.,0.,False)
            c['analytical_native']+=1;c['analytical_inflight_unknown']=False
            states.append(s.copy());controls.append(u.copy())
        states=np.asarray(states);controls=np.asarray(controls)
        lower=geometry.tube(states)
        rest=bool(abs(states[-1,[3,4,5]]).max()<=.003 and max(abs(x)for x in source.feedback.current(p)[2:])<=.03 and abs(p.adapter.last[2:]).max()<=1e-10)
        caps=bool((abs(states[:,3:6])<=np.asarray([.13,.03,.16])+1e-8).all())
        assert digest(packet)==before,'RESERVE_MUTATED_ACTUAL_SOURCE_PACKET'
        proof=dict(passed=bool(lower>=.22-1e-8 and rest and caps),before_native=packet['native_tick'],complete_native=200,
                   source_packet_sha256=before,causal_snapshot_sha256=self.snapshot_sha256,source_coefficient_native=forecast['periodic_source_tick'],
                   causal_tube_lower_m=lower,rest=rest,body_caps=caps,model_wheel_feedback='EXACT_MEASURED_T0_THEN_ORIGINAL_SCALAR_COORDINATES')
        return proof,states,controls
