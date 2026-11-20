"""Actual measured origin/control memory, original response-model braking only."""
import math
import time
import numpy as np
def certify(vehicle,setup,geometry,packet,Adapter,result,deadline):
    from coupled_model import Predictor,initial
    import kernel
    origin=packet(vehicle);p=Predictor(setup,initial(origin),kernel.PARAMETERS);p.adapter.__class__=Adapter;p.adapter.parked_target=None
    states=[p.state.copy()];controls=[]
    for _ in range(200):
        assert result['analytical_native']<300000 and time.time()<deadline-60,'PRIVATE_RESPONSE_LIMIT'
        s,u=p.step(0.,0.,False);result['analytical_native']+=1;states.append(s.copy());controls.append(u.copy())
    states=np.asarray(states);controls=np.asarray(controls);lower=geometry.tube(states,vehicle.count)
    rest=bool(abs(states[-1,[3,4,5]]).max()<=.003 and abs(states[-1,7])<=.03 and abs(p.adapter.last[2:]).max()<=1e-10)
    caps=bool((abs(states[:,3:6])<=np.asarray([.13,.03,.16])+1e-8).all())
    proof=dict(passed=bool(lower>=.22-1e-8 and rest and caps),before_native=vehicle.count,complete_native=200,causal_tube_lower_m=lower,rest=rest,body_caps=caps,source_packet=origin,source_coefficient_native=32200)
    return proof,states,controls
