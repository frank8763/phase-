"""Explicit no-model adapter state; does not call a model-aware constructor."""
import copy,importlib.abc,importlib.util,json,math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
spec=importlib.util.spec_from_file_location('v984_exact_frozen958',R/'experiments/v958_hold_steering_contract/vehicle_control.py')
frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)

def make(cls,setup=None):
    if setup is None:setup=json.loads((R/'runs/v983_saved_transient_diagnosis/physics/SETUP.json').read_text())
    limits=np.asarray(setup['limits'],float)
    instance=cls.__new__(cls)
    instance.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,
        legal=lambda command:bool(np.isfinite(command).all()and(command>=limits[:,0]-1e-10).all()and(command<=limits[:,1]+1e-10).all()))
    instance.dt=.01;instance.last=np.zeros(4);instance.integral=0.;instance.wheelbase=.6;instance.track=.54;instance.radius=.12
    instance.center_limit=.42722137342572125;instance.max_curvature=math.tan(instance.center_limit)/instance.wheelbase
    instance.mode='DRIVING';instance.encoders=None;instance.last_yaw_proof=None
    return instance

def copy_state(source,cls):
    target=make(cls)
    target.last=source.last.copy();target.integral=source.integral;target.mode=source.mode
    return target
