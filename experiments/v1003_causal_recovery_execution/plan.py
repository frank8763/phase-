"""Cause-selected recovery targets and an explicit, executable input schedule."""
import copy,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
from predictor import Predictor,virtual,virtual_rate
R=Path(__file__).resolve().parents[2]
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
search=load('v1003_exact_progress_search',R/'experiments/v1000_local_progress_reference/reference.py')
geometry=search.ref._old
PARAMETERS=json.loads((R/'experiments/v1002_causal_response_predictor/PARAMETERS.json').read_text())
SPEED=.03;EDGE_TICKS=334;BRAKE_TICKS=200

def initial_from_packet(packet,last_ctrl,integral):
    body=packet['body'];enc=packet['steering']
    return dict(state=[*body[:4],0.,body[4],virtual(enc['position']),virtual_rate(enc['position'],enc['velocity'])],
        last_ctrl=list(last_ctrl),integral=float(integral),virtual_rate=.6)

def predict(setup,initial,targets):
    assert 0<len(targets)<=12
    requests=[]
    for d in targets:
        assert abs(d)<=search.ref.MAX_DELTA+1e-12
        requests.extend([[SPEED,SPEED*math.tan(d)/.6,False] for _ in range(EDGE_TICKS)])
    requests.extend([[0.,0.,False] for _ in range(BRAKE_TICKS)])
    forecast=Predictor(setup,initial,PARAMETERS);states=[forecast.state.copy()];controls=[]
    for request in requests:
        state,u=forecast.step(*request);states.append(state);controls.append(u)
    return np.array(states),np.array(controls),requests

def construct(packet,source,goal,known,setup,last_ctrl,integral,deadline):
    proposal=search.construct(packet,source,goal,known,packet['body_measured_at'],deadline)
    base=dict(passed=False,status='FINITE_PROGRESS_SEARCH_REJECTED',source_proposal=proposal,models=0,mujoco_integrations=0,
        original_goal=list(goal),source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'])
    if not proposal['passed']:return base
    initial=initial_from_packet(packet,last_ctrl,integral)
    states,controls,requests=predict(setup,initial,proposal['edge_targets'])
    a,b=geometry.Geometry(known,source['periodic']).clearances(states[:,:3]);minimum=float(np.minimum(a,b).min())
    nominal=float(np.linalg.norm(states[0,:2]-goal)-np.linalg.norm(states[-1,:2]-goal));progress=nominal-.08
    stopped=bool(abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03)
    checks=dict(full_cycle=minimum>=search.ref.REQUIRED,progress=progress>=.4,complete_stop=stopped,
        speed=bool(abs(states[:,3]).max()<=.13),yaw_rate=bool(abs(states[:,5]).max()<=.16),finite=bool(np.isfinite(states).all()))
    return dict(base,passed=all(checks.values()),status='CAUSAL_PLANNED_INPUT_REFERENCE'if all(checks.values())else'PREDICTED_INPUT_REFERENCE_REJECTED',
        initial=initial,state_path=states.tolist(),path=states[:,:3].tolist(),planned_body_requests=requests,predicted_actuator_controls=controls.tolist(),
        edge_targets=proposal['edge_targets'],checks=checks,minimum_raw_full_cycle_clearance_m=minimum,required_raw_clearance_m=search.ref.REQUIRED,
        actual_goal_progress_lower_m=progress,nominal_goal_progress_m=nominal,analytical_prediction_steps=len(requests),
        movement_ticks=len(requests)-BRAKE_TICKS,brake_ticks=BRAKE_TICKS,physical_tracking_qualified=False,
        global_safety_bound=False,reference_and_execution_body_inputs_identical=True)
