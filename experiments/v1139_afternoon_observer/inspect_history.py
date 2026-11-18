"""Reconstruct recorded 20160 controller allocations without physical imports."""
import sys,json,math,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1139_afternoon_observer'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'));from bindings import Adapter,ref
import kernel,numpy as np
sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump

def main():
 root=R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/physics';s=json.loads((root/'SETUP.json').read_text());cmd=json.loads((root/'BODY_COMMANDS.json').read_text());z=np.load(root/'NATIVE_TRACE.npz');q=z['qpos'];vel=z['qvel'];ctrl=z['ctrl'][:,s['actuator_ids']];owner=kernel.Predictor(s,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),kernel.PARAMETERS).adapter;owner.__class__=Adapter;owner.virtual_rate=.6;maximum=0.;first=None
 for k in range(20160):
  enc=np.zeros(4)if k==0 else np.r_[q[k-1,s['steering_qpos_addresses']],vel[k-1,s['steering_qvel_addresses']]];owner.encoders=lambda enc=enc:enc.copy();owner.parked_target=None;_,v,w,mv,mw,stale=cmd[k];u=owner.compute(v,w,mv,mw,stale);e=float(abs(u-ctrl[k]).max());maximum=max(maximum,e)
  if e>1e-10 and first is None:first={'native':k,'error':e,'computed':u.tolist(),'stored':ctrl[k].tolist()}
 result={'passed':first is None,'historical_commands':20160,'maximum_controller_error':maximum,'first_mismatch':first,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'HISTORY_CONTROLLER_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
