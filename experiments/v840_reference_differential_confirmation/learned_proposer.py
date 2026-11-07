"""Behavior-cloned actuator target proposal, always subject to native safety gates."""
import hashlib,json
from pathlib import Path
import numpy as np

def features(env,path,index,current,steer,speed,last):
    path=np.asarray(path);target=path[min(index+12,len(path)-1)]
    rel=target[:2]-current[:2];c=np.cos(current[2]);s=np.sin(current[2]);angle=target[2]-current[2]
    return np.r_[c*rel[0]+s*rel[1],-s*rel[0]+c*rel[1],np.sin(angle),np.cos(angle),env.data.qvel[0]*c+env.data.qvel[1]*s,env.data.qvel[5],np.asarray(last)/[.52,.52,20.,20.],steer,speed]

class Proposer:
    def __init__(self,path):
        p=Path(path);self.sha256=hashlib.sha256(p.read_bytes()).hexdigest();self.parameters=json.loads(p.read_text())
        self.mean=np.asarray(self.parameters['mean']);self.std=np.asarray(self.parameters['std'])
        assert self.mean.shape==self.std.shape==(12,)
    def predict(self,x):
        z=np.clip((np.asarray(x)-self.mean)/self.std,-5.,5.)
        for layer in self.parameters['layers']:
            z=np.tanh(z@np.asarray(layer['weight']).T+np.asarray(layer['bias']))
        target=z*np.array([.52,.52,20.,20.]);assert target.shape==(4,)and np.isfinite(target).all()
        return target
