"""Transplant original nominal proposal rules; model-free adapter only."""
import ast, math
from pathlib import Path
from types import SimpleNamespace, MethodType
import numpy as np
from learned_proposer import Proposer

own = Path(__file__).parent
namespace = dict(np=np, math=math)
tree = ast.parse((own/'legacy_source.py').read_text())
cls = next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='RobotPredictor')
choose = next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='select')
project=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='project_to_segment_path')
exec(compile(ast.Module(body=[project],type_ignores=[]),str(own/'legacy_source.py'),'exec'),namespace)
exec(compile(ast.Module(body=[choose],type_ignores=[]),str(own/'legacy_source.py'),'exec'),namespace)
tree = ast.parse((own/'ackermann_source.py').read_text())
ack = next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body
           if isinstance(n,ast.FunctionDef) and n.name=='_ackermann_from_steer_speed')
exec(compile(ast.Module(body=[ack],type_ignores=[]),str(own/'ackermann_source.py'),'exec'),namespace)
select_original = namespace['select']

def environment(real, model):
    inner=SimpleNamespace(wheel_radius=.12,wheel_base=.6,track_width=.54,diff_gain=8.,
        max_steer=math.radians(40),max_wheel_speed=48.,
        id_lf_steer=0,id_rf_steer=1,id_lr_wheel=2,id_rr_wheel=3)
    inner._ackermann_from_steer_speed=MethodType(namespace['_ackermann_from_steer_speed'],inner)
    return SimpleNamespace(inner=inner,data=real,model=model)

def guidance(path,current,index):
    index += int(np.argmin(np.linalg.norm(path[index:min(index+40,len(path)),:2]-current[:2],axis=1)))
    target_index=min(index+1,len(path)-1);arc=0.
    while target_index<len(path)-1 and arc<.45:
        arc+=float(np.linalg.norm(path[target_index+1,:2]-path[target_index,:2]));target_index+=1
    rel=path[target_index,:2]-current[:2]
    lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
    steer=float(np.clip(math.atan2(1.2*lateral,max(float(rel@rel),.02)),-math.radians(40),math.radians(40)))
    speed=min(.60,.50/(1+abs(steer)))
    return index,steer,speed

def schedule(parameters,last,command_map):
    return command_map.sequence(np.asarray(parameters),last,328,80)

class OriginalNominal:
    select=select_original
    def __init__(self,command_map,proposer,callback):
        self.command_map=command_map;self.proposer=proposer;self.callback=callback
        self.prediction_steps=0
    def predict(self,real,target,ids,last,horizon=240,brake_after=80):
        assert horizon==240 and brake_after==80
        z=self.callback(np.asarray(target));self.prediction_steps+=328
        from self_geometry import containment_margin
        self.prediction_self_margin=float(containment_margin(z['self_bounds'][:241],np.array([-.44,-.375,.44,.375])).min())
        self.prediction_self_contained=self.prediction_self_margin>=.002
        self.terminal_speed=float(np.linalg.norm(z['qvel'][239,:2]))
        return z['poses'][:240]
