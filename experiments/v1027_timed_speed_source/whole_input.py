"""Predict the WHOLE frozen-controller input schedule; never accepts a prefix."""
import importlib.util,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1003_causal_recovery_execution'))
from predictor import Predictor,virtual,virtual_rate
PARAMETERS=json.loads((R/'experiments/v1002_causal_response_predictor/PARAMETERS.json').read_text())
EDGE_TICKS=334;BRAKE_TICKS=200;MAX_EDGES=100

def public_setup(setup):
    """Only public map/actuator metadata; actor truth is never planner input."""
    return {name:setup[name]for name in ('known','limits','slew_per_second')}

def initial(packet):
    b=packet['body'];s=packet['steering'];memory=packet['controller_memory']
    return dict(state=[*b[:4],0.,b[4],virtual(s['position']),virtual_rate(s['position'],s['velocity'])],last_ctrl=memory['last_ctrl'],integral=memory['integral'],virtual_rate=.6)

def predict(setup,packet,targets):
    assert 0<len(targets)<=MAX_EDGES
    engine=Predictor(setup,initial(packet),PARAMETERS);states=[engine.state.copy()];controls=[];requests=[]
    for target in targets:
        assert abs(target)<=.42722137342572125+1e-12
        request=[.03,.03*math.tan(target)/.6,False]
        for _ in range(EDGE_TICKS):
            state,control=engine.step(*request);states.append(state);controls.append(control);requests.append(request)
    for _ in range(BRAKE_TICKS):
        state,control=engine.step(0.,0.,False);states.append(state);controls.append(control);requests.append([0.,0.,False])
    return np.asarray(states),np.asarray(controls),np.asarray(requests,float)

def checks(states,controls,requests,packet,setup,goal,raw_clearance,required):
    n=len(requests);limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    upper=float(np.linalg.norm(states[-1,:2]-goal))+.08
    return dict(full_trajectory_and_tail=len(states)==n+1 and len(controls)==n and n>200,
        finite=bool(np.isfinite(states).all()and np.isfinite(controls).all()and np.isfinite(requests).all()),
        full_raw_geometry=bool(raw_clearance>=required),goal_upper=upper<=.45,
        complete_stop=bool(abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03),
        exact_200_stop_inputs=bool(np.array_equal(requests[-200:],np.zeros((200,3)))),
        speed_yaw=bool(abs(states[:,3]).max()<=.13 and abs(states[:,5]).max()<=.16 and abs(states[:,4]).max()<=.03),
        legal_ctrl=bool(np.all(controls>=limits[:,0]-1e-10)and np.all(controls<=limits[:,1]+1e-10)),
        legal_slew=bool(np.all(abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],controls]),axis=0))<=rate+1e-10))),upper
