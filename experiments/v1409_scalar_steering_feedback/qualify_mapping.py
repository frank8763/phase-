"""Only read saved arrays; no model import, construction or integration."""
import ast
import hashlib
import importlib.abc
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','coupled_model','factory','physical','rclpy'}:raise AssertionError('NO_MODEL_COORDINATE_QUALIFICATION:'+name)
sys.meta_path.insert(0,NoModel())
from feedback import current,from_state


def main():
    assert sorted(os.sched_getaffinity(0))==[4];os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    import numpy as np
    model=R/'runs/v1408_saved_capture_witness/model';packet=json.loads((model/'CURRENT_INPUT.json').read_text())['origin']
    with np.load(model/'NOMINAL.npz',allow_pickle=False)as z:states=z['states']
    # Execute the original V1393 enc(s) AST as an independent formula source.
    path=R/'experiments/v1393_full9390_preparation/analysis.py';node=next(n for n in ast.walk(ast.parse(path.read_text()))if isinstance(n,ast.FunctionDef)and n.name=='enc');scope=dict(math=math);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),scope)
    maxerr=0.
    for s in states:maxerr=max(maxerr,max(abs(a-b)for a,b in zip(from_state(s),scope['enc'](s))))
    assert maxerr<=1e-15
    p=SimpleNamespace(steps=0,high_speed_episode=False,front=np.asarray(packet['steering']['position']),front_rate=np.asarray(packet['steering']['velocity']),state=states[0].copy())
    assert np.asarray(current(p)).tobytes()==np.asarray([*packet['steering']['position'],*packet['steering']['velocity']]).tobytes()
    initial_projection=max(abs(a-b)for a,b in zip(from_state(states[0]),current(p)))
    p.steps=len(states)-1;p.state=states[-1].copy();final=current(p);pair=[math.atan(-.3/(1+.135)),math.atan(-.3/(1-.135))]
    assert max(abs(a-b)for a,b in zip(final[:2],pair))<=1e-12 and max(abs(x)for x in final[2:])<=.03
    negative=[]
    for name,mutate in [('uncovered_model_steps',lambda:setattr(p,'steps',-1)),('unsupported_high_speed_episode',lambda:(setattr(p,'steps',1),setattr(p,'high_speed_episode',True)))]:
        mutate()
        try:current(p)
        except AssertionError:negative.append(name)
        else:raise AssertionError('INVALID_COORDINATE_MODE_ACCEPTED')
    result=dict(passed=True,saved_state_mapping_points=len(states),original_v1393_formula_maximum_error=maxerr,
                exact_measured_origin_bits_preserved=True,initial_projection_residual_rad=initial_projection,
                final_original_preparation_target_angle_error_rad=max(abs(a-b)for a,b in zip(final[:2],pair)),final_model_wheel_velocity_max=max(abs(x)for x in final[2:]),
                negative_cases=negative,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,not_complete_response_qualification=True)
    (O/'MAPPING_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    files=[C/'feedback.py',C/'qualify_mapping.py',C/'PROTOCOL.md',path,model/'NOMINAL.npz',model/'CURRENT_INPUT.json']
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},physical_admission=False),indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
