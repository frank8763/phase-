"""Regression: a settled car short of a cusp must be able to change gear.
No switching while moving, misaligned, outside tolerance, or at a terminal goal.
"""
import json
import numpy as np
from tracking import switch_if_settled
path=np.array([[i*.04,0.,0.,1 if i<=6 else -1]for i in range(13)])
current=np.array([.11,0.,0.]);index=3
new,event=switch_if_settled(path,index,current,np.zeros(6));assert new==6 and event['to_gear']==-1
for pose,v in [(current,np.array([.06,0,0,0,0,0])),(np.array([.11,0,.3]),np.zeros(6)),(np.array([0.,0,0]),np.zeros(6))]:
    new,event=switch_if_settled(path,index,pose,v);assert new==index and event is None
new,event=switch_if_settled(path,8,np.array([.48,0,0]),np.zeros(6));assert new==8 and event is None
print(json.dumps({'status':'PASS','cases':5,'simulation_steps':0,'training_updates':0}))
