"""Native receive/execution monitor, same real vehicle actuation; no root writes."""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import Startup as OriginalStartup,require
from command_tube import nominal,MAX_BODY_SPEED,MAX_BODY_YAW_RATE,DELIVERY_S
class Startup(OriginalStartup):
    def receive(self,packet,now,native_tick,sim_time):
        if packet.get('kind')=='command':
            proof=packet.get('tube',{})
            require(proof.get('passed') is True,'COMMAND_WITHOUT_TUBE')
            require(proof['v']==packet['v'] and proof['w']==packet['w'],'COMMAND_PROOF_MISMATCH')
            require(proof['issued_at']==packet['issued_at'],'COMMAND_TIME_MISMATCH')
            require(0<=now-packet['issued_at']<=DELIVERY_S,'COMMAND_DELIVERY_BUDGET')
            require(proof['source_native_tick']<=proof['body_native_tick']<=native_tick,'COMMAND_FUTURE_SOURCE')
        return super().receive(packet,now,native_tick,sim_time)
    def step(self,vehicle,now):
        if self.command is not None:
            p=self.command['tube'];next_elapsed=(vehicle.count+1-p['body_native_tick'])*.01
            from cycle_backup import retained_allowed
            require(retained_allowed(p,next_elapsed),'FINITE_COMMAND_PERMISSION_EXPIRED')
        super().step(vehicle,now)
        body=vehicle.body()
        require(abs(body[3])<=MAX_BODY_SPEED and abs(body[4])<=MAX_BODY_YAW_RATE,'EMPIRICAL_BODY_BOUND_EXCEEDED')
        if self.command is None:return
        proof=self.command['tube'];elapsed=(vehicle.count-proof['body_native_tick'])*.01
        predicted=nominal(proof['body'],proof['v'],proof['w'],[elapsed])[0]
        # This explicitly checks empirical assumptions in execution, independently
        # of the obstacle geometry and final native clearance audit.
        p=float(np.linalg.norm(np.asarray(body[:2])-predicted[:2]))
        a=abs(math.atan2(math.sin(body[2]-predicted[2]),math.cos(body[2]-predicted[2])))
        delay=proof['body_age_s']+DELIVERY_S
        require(p<=proof['residual_position_m']+MAX_BODY_SPEED*delay+1e-8,'EMPIRICAL_TRANSLATION_TUBE_EXCEEDED')
        require(a<=proof['residual_angle_rad']+MAX_BODY_YAW_RATE*delay+1e-8,'EMPIRICAL_ROTATION_TUBE_EXCEEDED')
