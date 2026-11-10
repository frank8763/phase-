"""Explicit metadata only; production class constructor is not executed."""
import importlib.abc
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

R=Path(__file__).resolve().parents[2]
O=R/'runs/v993_steering_transient_diagnosis'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
spec=importlib.util.spec_from_file_location('v990_historical_adapter',R/'experiments/v958_hold_steering_contract/vehicle_control.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def make(cls,setup=None):
    setup=setup or json.loads((O/'saved_v987/physics/SETUP.json').read_text())
    limits=np.array(setup['limits'],float)
    obj=cls.__new__(cls)
    obj.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,
        legal=lambda u:bool(np.isfinite(u).all()and np.all(u>=limits[:,0]-1e-10)and np.all(u<=limits[:,1]+1e-10)))
    obj.dt=.01;obj.last=np.zeros(4);obj.integral=0.;obj.wheelbase=.6;obj.track=.54;obj.radius=.12
    obj.center_limit=.42722137342572125;obj.max_curvature=math.tan(obj.center_limit)/obj.wheelbase
    obj.mode='DRIVING';obj.encoders=None;obj.last_allocation_proof=None
    return obj
