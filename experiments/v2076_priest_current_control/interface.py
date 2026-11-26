"""One origin-bound PRIEST preview; no gear, Allocator or plant authority."""
from pathlib import Path
import copy, hashlib, importlib.util, math
import json

R=Path(__file__).resolve().parents[2]
OLD=R/'experiments/v1485_priest_current_polynomial_seam'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class OriginPreview:
    def __init__(self,current,proposal,source,*,archived_software_only=False):
        self.closed=False
        self.used=False
        self.poisoned=True
        for path in [OLD/'polynomial.py', OLD/'candidate_output.py', OLD/'response_policy.py',R/'experiments/v1288_baseline_interface/contract.py']:
            assert source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'PRIEST_CONTROL_SOURCE_CHANGED'
        if archived_software_only:
            assert current['kind']=='PHASE_ARCHIVED_CAUSAL_PRIEST_T0_INPUT'
        else:
            assert current['kind']=='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT','PRIEST_ARCHIVED_INPUT_NOT_CURRENT'
        self.current=copy.deepcopy(current)
        self.proposal=copy.deepcopy(proposal)
        self.boundary=load('PRIEST_exact_origin_candidate',OLD/'candidate_output.py')
        rebuilt=self.boundary.bind(current,proposal['reply'])
        assert rebuilt==proposal,'PRIEST_PROPOSAL_BOUNDARY_CHANGED'
        self.poly=load('PRIEST_exact_polynomial',OLD/'polynomial.py')
        self.contract=load('PRIEST_exact_original_twist',R/'experiments/v1288_baseline_interface/contract.py')
        self.poisoned=False

    def preview(self,packet):
        assert not self.closed and not self.used and not self.poisoned,'PRIEST_CONTROL_CLOSED_USED_OR_POISONED'
        self.poisoned=True
        current=self.current
        assert digest(packet)==digest(current['origin']),'PRIEST_CONTROL_FOREIGN_MEASUREMENT'
        assert packet['native_tick']==current['fixed_origin_native'] and packet['sim_time']==current['fixed_origin_sim_time'],'PRIEST_CONTROL_ORIGIN_CLOCK_CHANGED'
        assert not packet['steering_motion_active'] and packet.get('parked_target') is None,'PRIEST_CONTROL_ACTIVE_STEERING_MODE'
        reply=self.proposal['reply']
        # Exact first-preview law already declared in V1485 Policy.select.
        # Raw reference derivatives are not actuator commands or certificates.
        samples=[self.poly.sample(reply['coefficients_x'],reply['coefficients_y'],time_s=i*10./99.,gear=reply['gear'])for i in range(6)]
        vx=sum(x['velocity'][0]for x in samples)/6
        vy=sum(x['velocity'][1]for x in samples)/6
        speed=math.hypot(vx,vy)
        assert speed>1e-12,'PRIEST_UNRESOLVED_ZERO_SPEED_DIRECTION'
        desired=math.atan2(reply['gear']*vy,reply['gear']*vx)
        error=math.atan2(math.sin(desired-packet['body'][2]),math.cos(desired-packet['body'][2]))
        vr=reply['gear']*speed*math.cos(error)
        wr=error/(6*10.*.01)
        assert abs(vr)<.005 or vr*reply['gear']>0,'PRIEST_REQUEST_OPPOSES_DECLARED_SEGMENT_GEAR'
        self.contract.twist(vr,wr)
        self.used=True
        self.poisoned=False
        return dict(raw_request=[vr,wr,False],input_sha256=current['input_sha256'],proposal_sha256=self.proposal['proposal_sha256'],origin_packet_sha256=digest(packet),origin_native=packet['native_tick'],original_gear_gate_still_required=True,full5_plus2200_response_still_required=True,actual_execution_permitted=False,full_vehicle_qualified=False)

    def close(self):
        self.closed=True
