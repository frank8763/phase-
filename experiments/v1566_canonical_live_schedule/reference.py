"""Immutable complete nominal monitor; no model, action or live admission."""
import hashlib
import math
import struct

def finite(values,n):
    assert isinstance(values,(tuple,list))and len(values)==n
    assert all(type(v)in(int,float)and math.isfinite(v)for v in values)

def rear(body):
    return body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]

class FixedResponse:
    def __init__(self,*,states,origin_native,origin_sim_time,expected_state_bytes_sha256,method_sha256):
        assert type(origin_native)is int and origin_native>=0
        assert isinstance(states,(list,tuple))and len(states)==13601
        for state in states:finite(state,8)
        # SHA is of the original float64 little-endian value bytes, preserving
        # signed zero. It must come from the full verified nominal DATA record.
        identity=hashlib.sha256()
        for state in states:identity.update(struct.pack('<8d',*state))
        assert identity.hexdigest()==expected_state_bytes_sha256
        self.states=tuple(tuple(state)for state in states)
        self.origin=origin_native;self.sim_origin=origin_sim_time
        self.method_sha256=method_sha256;self.state_bytes_sha256=identity.hexdigest()
        self.previous_index=0;self.previous_native=origin_native-1

    def assess(self,body,native_tick):
        finite(body,5)
        assert type(native_tick)is int and native_tick>self.previous_native
        index=native_tick-self.origin
        assert 0<=index<len(self.states)
        actual=rear(body);best=None
        for candidate in range(max(self.previous_index,0,index-20),min(len(self.states)-1,index+20)+1):
            expected=rear(self.states[candidate])
            distance=math.dist(actual[:2],expected[:2])
            yaw=abs(math.atan2(math.sin(actual[2]-expected[2]),math.cos(actual[2]-expected[2])))
            if distance<=.02+1e-8 and yaw<=.1+1e-8:
                rank=(abs(index-candidate),candidate,distance,yaw)
                if best is None or rank<best:best=rank
        assert best is not None,'ACTUAL_RESPONSE_OUTSIDE_FIXED_TIME_POSE_TUBE'
        self.previous_index=best[1];self.previous_native=native_tick
        return dict(reference_index=best[1],rear_error_m=best[2],yaw_error_rad=best[3],time_error_s=best[0]*.01,
            response_method_sha256=self.method_sha256,reference_state_bytes_sha256=self.state_bytes_sha256,
            physical_admission=False)
