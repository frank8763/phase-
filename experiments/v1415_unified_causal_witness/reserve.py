"""Current measured packet -> original full200 zero branch; no launch rights."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback
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
    def __init__(self,*,setup,current,authority,lock,accounting,save_complete,save_partial):
        self.setup=copy.deepcopy(setup);self.current=copy.deepcopy(current);self.snapshot=copy.deepcopy(current['causal_snapshot'])
        self.save_complete=save_complete;self.save_partial=save_partial
        assert callable(save_complete)and callable(save_partial)
        self.geometry=exact('v1415_current_geometry_binding',Path(__file__).with_name('geometry_binding.py')).GeometryBinding(current,setup)
        self.authority=copy.deepcopy(authority);self.lock=lock;self.accounting=accounting
        self.snapshot_sha256=digest(self.snapshot)
        # Preparation is complete before a new live command/wire is requested.
        # Repo sources are read-only inside run_phase; full hashes are checked
        # again by the outer owner on closure. No expiry gate is relaxed.
        hashes=self.authority['tested_source_hashes']
        assert hashes and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
        self.preverified_sources_sha256=digest(hashes)

    def __call__(self,packet,modes):
        a=self.authority;c=self.accounting
        parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
        assert a['scope']=='CURRENT_MEASURED_PACKET_RESERVE' and a['models_authorized'] is True
        assert a['round_id']==parent['active_round'] and parent['models_now_authorized']
        assert os.environ.get('PHASE_REPO')==str(R) and sorted(os.sched_getaffinity(0))==[2]
        assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()==parent['boot_id']
        assert a['absolute_deadline_unix']<=1795395600 and a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        assert Path('/proc/self/fd/'+str(self.lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert digest(a['tested_source_hashes'])==self.preverified_sources_sha256
        assert digest(self.snapshot)==self.snapshot_sha256==a['causal_snapshot_sha256']
        assert self.current['input_sha256']==a['current_input_sha256']
        assert abs(packet['sim_time']-(self.geometry.origin_sim_time+(packet['native_tick']-self.geometry.origin_native)*.01))<=1e-8,'RESERVE_CLOCK_CHANGED_FROM_FIXED_EVENT'
        assert modes['covered_native']==packet['native_tick']
        assert all(packet[k]==modes[k] for k in ['coupled_episode','steering_motion_active','parked_target'])
        assert not c.get('analytical_inflight_unknown',False) and not c.get('construction_inflight_unknown',False)
        assert c['analytical_native']+200<=a['maximum_analytical_native']
        assert c['predictor_constructions']<a['maximum_predictor_constructions']
        source=exact('v1415_original_scalar_generator',R/'experiments/v1410_scalar_feedback_witness/generator.py')
        Predictor,initial,kernel,Adapter,Geometry,_,_=source.binding()
        import numpy as np
        before=digest(packet)
        states=[];controls=[]
        try:
            c['construction_inflight_unknown']=True
            p=Predictor(self.setup,initial(packet),kernel.PARAMETERS)
            c['predictor_constructions']+=1;c['construction_inflight_unknown']=False
            assert p.adapter.__class__ is Adapter
            p.adapter.encoders=lambda owner=p:source.feedback.current(owner)
            p.adapter.parked_target=None
            # Closing the parked target is the prospective zero branch only;
            # coupled_episode remains the actual canonical-t0 tracked episode.
            p.adapter._steering_motion_active=packet['steering_motion_active']
            assert p.coupled_episode==packet['coupled_episode']
            assert np.array_equal(source.feedback.current(p),[*packet['steering']['position'],*packet['steering']['velocity']])
            states=[p.state.copy()]
            for _ in range(200):
                assert time.time()<a['absolute_deadline_unix']-30 and time.monotonic()<a['hard_stop_monotonic']-30
                c['analytical_inflight_unknown']=True;s,u=p.step(0.,0.,False)
                c['analytical_native']+=1;c['analytical_inflight_unknown']=False
                states.append(s.copy());controls.append(u.copy())
            states=np.asarray(states);controls=np.asarray(controls)
            lower=self.geometry.tube(states,packet['native_tick'])
            rest=bool(abs(states[-1,[3,4,5]]).max()<=.003 and max(abs(x)for x in source.feedback.current(p)[2:])<=.03 and abs(p.adapter.last[2:]).max()<=1e-10)
            caps=bool((abs(states[:,3:6])<=np.asarray([.13,.03,.16])+1e-8).all())
            assert digest(packet)==before,'RESERVE_MUTATED_ACTUAL_SOURCE_PACKET'
            proof=dict(passed=bool(lower>=.22-1e-8 and rest and caps),before_native=packet['native_tick'],complete_native=200,
                       source_packet_sha256=before,causal_snapshot_sha256=self.snapshot_sha256,source_coefficient_native=self.snapshot['periodic']['source_tick'],current_input_sha256=self.current['input_sha256'],geometry_kind=self.geometry.geometry_kind,
                       causal_tube_lower_m=lower,rest=rest,body_caps=caps,model_wheel_feedback='EXACT_MEASURED_T0_THEN_ORIGINAL_SCALAR_COORDINATES')
            self.save_complete(proof,states,controls)
            return proof,states,controls
        except BaseException as exc:
            evidence=dict(before_native=packet['native_tick'],source_packet=copy.deepcopy(packet),first_error=repr(exc),traceback=traceback.format_exc(),accounting=copy.deepcopy(c),current_input_sha256=self.current['input_sha256'],geometry_kind=self.geometry.geometry_kind,complete_certificate=False)
            try:self.save_partial(evidence,np.asarray(states),np.asarray(controls))
            except BaseException as saving:c['partial_save_error']=repr(saving)
            raise
