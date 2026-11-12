"""Reuse the qualified live discovery owner; replace recovery with pose feedback."""
import sys,json,time,math
from pathlib import Path
import numpy as np
from kernel import load,virtual
from physical_ops import bind,dump
from braking_reserve import Adapter
import live_reference as live
R=Path(__file__).resolve().parents[2]

def configure(output):
 import kernel
 kernel.O=Path(output)
 import planner
 planner.O=Path(output)
 import owner
 return owner

def execute(v,setup,original,end,evidence,out,packet_fn,output):
 import mujoco as mj
 origin=v.count;packet=packet_fn(v,True);source=evidence.source(v);assert evidence.first is not None and packet['native_tick']==source['source_native_tick']
 bind(v,Adapter,mj);packet=packet_fn(v,True);packet['speed_episode']=False;goal=original['goal'];start=time.monotonic();proposal=live.produce(setup,packet,source,output,goal)
 dump(out/'LIVE_ENTRY.json',dict(packet=packet,source=source,goal=goal));dump(out/'LIVE_SOURCE_PROOF.json',dict(chosen=proposal['proof'],candidates=proposal['candidates'],static=proposal['static']));reference=proposal['reference'];np.savez_compressed(out/'LIVE_REFERENCE.npz',nominal_states=proposal['nominal_states'],nominal_requests=proposal['nominal_requests']);np.savez_compressed(out/'LIVE_WAIT.npz',states=proposal['wait_states'],controls=proposal['wait_controls'],requests=proposal['wait_requests']);dump(out/'LIVE_BOUNDARY.json',dict(native=origin,mode_switch_state_neutral=True,source_native_tick=source['source_native_tick'],source_frozen_not_refreshed=True))
 maximum=np.zeros(3);crossmax=0.;vmax=0.;waits=proposal['wait_requests'];ss=proposal['wait_states'];wait_meta=dict(start_native=v.count,executed_native=0,packet=packet)
 def step(req,expected,on_path):
  nonlocal maximum,crossmax,vmax
  assert time.time()<end-120,'FULL_OWN_REPLAY_RESERVE';v.step(*req);body=np.array(v.body());angle=body[2]-expected[2];e=np.array([np.linalg.norm(body[:2]-expected[:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-expected[6])]);maximum=np.maximum(maximum,e);assert np.all(e<=[.04,.035,.015]),'FRESH_POSE_PREDICTION_TRACKING';vmax=max(vmax,abs(body[3]));assert abs(body[3])<=.13 and abs(body[4])<=.16,'FRESH_BODY_CAP'
  if on_path:
   cross=float(np.linalg.norm(reference.path[:,:2]-body[:2],axis=1).min());crossmax=max(crossmax,cross);assert cross<=.04,'FRESH_REFERENCE_CROSS_TRACK'
  if v.count%5==0:evidence.update(v.scan())
 for i,r in enumerate(waits):step(r,ss[i+1],False);wait_meta['executed_native']+=1
 dump(out/'LIVE_WAIT_EXECUTION.json',wait_meta);blocks=[];progress=0;moving=0;stopped=False;cert=out/'certificates';cert.mkdir()
 while not stopped:
  assert moving<live.MAX_ACTIVE,'REGISTERED_ACTIVE_BUDGET';p=packet_fn(v,True);p['speed_episode']=bool(getattr(v.adapter,'_speed_episode',False));proof,ss,uu,rr,indices=reference.complete(setup,p,source,progress,live.MAX_ACTIVE-moving);number=len(blocks);prefix=min(live.BLOCK,proof['active_native'])if proof['active_native']else live.STOP;stopped=proof['active_native']==0
  row=dict(number=number,start_native=v.count,packet=p,source_native_tick=source['source_native_tick'],source_age_s=p['sim_time']-source['periodic']['last'],progress=progress,remaining_active=live.MAX_ACTIVE-moving,executed_native=0,planned_prefix=prefix,proof=proof);dump(cert/f'{number}.json',row);np.savez_compressed(cert/f'{number}.npz',states=ss,controls=uu,requests=rr,progress=indices);assert proof['passed'],'COMPLETE_LIVE_FUTURE_REJECTED';blocks.append(row);dump(out/'BLOCKS.json',blocks)
  for i,r in enumerate(rr[:prefix]):step(r,ss[i+1],True);row['executed_native']+=1
  progress=int(indices[prefix-1]);moving+=0 if stopped else prefix;dump(cert/f'{number}.json',row);dump(out/'BLOCKS.json',blocks);dump(out/'PARTIAL.json',dict(phase='FRESH_COMPLETE_POSE_FEEDBACK',native=v.count,recovery_native=v.count-origin,moving_native=moving,certificates=len(blocks),maximum_local_tracking=maximum.tolist()))
 return dict(passed=True,root_native=origin,source_native_tick=source['source_native_tick'],recovery_native=v.count-origin,wait_native=len(waits),moving_native=moving,complete_stop_native=live.STOP,maximum_local_tracking=maximum.tolist(),maximum_path_cross_track_m=crossmax,maximum_actual_speed=vmax,recovery_wall_s=time.monotonic()-start)
