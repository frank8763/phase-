"""Actual RPP FollowPath curve-stop and continuous forward path; no actuator bypass."""
import copy
import math
import time
import sys
from types import SimpleNamespace
import numpy as np
from pathlib import Path
K=.758770385

def path_step(pose,distance,k):
    x,y,a=pose;b=a+k*distance
    if abs(k)<1e-12:return[x+distance*math.cos(a),y+distance*math.sin(a),b]
    return[x+(math.sin(b)-math.sin(a))/k,y-(math.cos(b)-math.cos(a))/k,b]

def curve_path(start):
    return[path_step(start,s,K)for s in np.linspace(0.,.20,201)]

def continuation_path(packet):
    from steering_continuity import measured
    _,_,pair=measured(packet,packet['body_measured_at']);assert abs(pair[0]-pair[1])<=.02
    initial=float(np.mean(pair));assert abs(initial)<=K+2e-6
    delta=math.atan(.6*max(-K,min(K,initial)));result=[list(packet['body'][:3])]
    # Reference is spatial, not a time-arrival demand. Nominal.1m/s maps the
    # original.60rad/s steering limit to a6rad/m curvature transition.
    for i in range(1200):
        midpoint=(i+.5)*.001;angle=math.copysign(max(0.,abs(delta)-6.*midpoint),delta)
        result.append(path_step(result[-1],.001,math.tan(angle)/.6))
    return result

def run(node,until,deadline,spin,wait,require,check_servers):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(Path(__file__).parent),str(root/'experiments/v939_rpccr_rpp_handoff'),str(root/'experiments/v938_rpccr_recovery_segments')]
    from binding import FollowPathBinding
    from transaction import fingerprint
    from steering_continuity import stopped_ready
    rows=[]
    def tick():
        spin(node,timeout_sec=.005);check_servers()
        require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure))
        require(time.monotonic()<until and time.time()<deadline-25,'CLOSED_HANDOFF_DEADLINE')
    def snapshot():
        p,s=node.motion.decision_snapshot();return copy.deepcopy(p),copy.deepcopy(s)
    def settle():
        stable=None
        while True:
            tick();p,s=snapshot();now=time.monotonic()
            if stopped_ready(p,now):
                stable=now if stable is None else stable
                if now-stable>=.5:return p,s
            else:stable=None
    def follow(path,label,generation_packet):
        p,s=snapshot();binding=FollowPathBinding(node)
        wait(node,binding.client.server_is_ready,min(until,time.monotonic()+2.),'FOLLOW_SERVER_TIMEOUT')
        future=binding.send(dict(action='SEND_FOLLOW_PATH_ONCE',path=path,path_sha256=fingerprint(path)))
        wait(node,future.done,min(until,time.monotonic()+2.),'FOLLOW_ACCEPT_TIMEOUT')
        handle=future.result();require(handle.accepted,'CLOSED_HANDOFF_FOLLOW_REJECTED');result=handle.get_result_async()
        while not result.done():tick()
        status=result.result().status;require(status==4,'CLOSED_HANDOFF_FUNCTIONAL_FAILURE')
        end,source=settle()
        row=dict(label=label,path=path,path_generation_packet=copy.deepcopy(generation_packet),start_packet=p,start_source=s,end_packet=end,end_source=source,follow_status=status)
        rows.append(row);save();return row
    def save():
        p=Path(node.motion.out)/'CLOSED_HANDOFF.json'
        import json
        p.write_text(json.dumps(dict(stages=rows,actuator_source='Actual installed FeasibleRPP FollowPath plus existing pre-admission steering shaper and original safety/native gates'),indent=2)+'\n')
    begin,_=settle();first=follow(curve_path(begin['body'][:3]),'CURVE_STOP',begin)
    stopped=first['end_packet'];q=np.asarray(stopped['steering']['position'])
    require(np.linalg.norm(np.asarray(stopped['body'][:2])-begin['body'][:2])>=.12,'CURVE_NOT_ACTUALLY_DRIVEN')
    require(abs(q).max()>=.20,'HELD_CURVED_STEERING_NOT_EXERCISED')
    second=follow(continuation_path(stopped),'CONTINUOUS_FORWARD_RPP',stopped)
    return SimpleNamespace(status=4,result=SimpleNamespace(error_code=0)),rows
