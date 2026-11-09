"""Exact native certificate/control seam with a recording stub, zero physical models."""
import copy,importlib.abc,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v916_cycle_backup'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from native_contract import Startup
class Recorder:
 def __init__(self,body,count):self.value=body;self.count=count;self.calls=[]
 def body(self):return self.value
 def step(self,v,w,stale):self.calls.append([v,w,stale]);self.count+=1
base=dict(passed=True,v=.1,w=0.,body_native_tick=10,body=[0.,0.,0.,.1,0.],body_age_s=.001,issued_at=100.,residual_position_m=.02,residual_angle_rad=.035,terminal_cycle_qualified=True,terminal_cycle_lower_m=.2)
s=Startup('test');s.phase='RUNNING';s.armed_at=100.;s.command=dict(issued_at=100.,v=.1,w=0.,tube=base);v=Recorder([.02,0.,0.,0.,0.],510);s.step(v,105.)
checks=dict(retained_motion_becomes_only_zero_after_commit=v.calls==[[0.,0.,True]],retained_anchor_not_reset=s.command['tube']['body_native_tick']==10)
for label,proof,body in [('finite_expiry',dict(base,terminal_cycle_qualified=False),[.02,0.,0.,0.,0.]),('translation_violation',base,[.06,0.,0.,0.,0.]),('rotation_violation',base,[.02,0.,.06,0.,0.]),('speed_violation',base,[.02,0.,0.,.14,0.])]:
 ss=Startup('test');ss.phase='RUNNING';ss.armed_at=100.;ss.command=dict(issued_at=100.,v=.1,w=0.,tube=proof)
 try:ss.step(Recorder(body,510),105.)
 except Exception:checks[label+'_stops']=True
 else:checks[label+'_stops']=False
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,stub_only=True);(O/'NATIVE_SEAM_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
