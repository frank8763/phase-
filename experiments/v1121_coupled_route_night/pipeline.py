"""Preserve successful normal owner; causal full-state recovery on refusal only."""
import sys,json,time,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
from bindings import Adapter,REQUIRED,ref
import fresh_pipeline as normal
import live_reference as live
from physical_ops import bind,dump
from source import Engine,Predictor,initial,python_replay,remaining_rows,requests,solve,final_gate,digest,COUNTS,SourceRefusal
from recovery_source import forecast_packet
import numpy as np
import kernel

def configure(output):return normal.configure(output)
def front_rows(rows,n):
 assert isinstance(n,int)and 0<n<=sum(int(r[2])for r in rows),'INVALID_PREFIX_NATIVE'
 out=[]
 for t,v,k,m in rows:
  take=min(n,int(k))
  if take:out.append((t,v,take,m));n-=take
  if not n:break
 assert n==0;return out

def extended_packet(v,packet_fn,episode):
 p=packet_fn(v,True);yaw=p['body'][2];p['body_lateral']=float(-v.d.qvel[0]*math.sin(yaw)+v.d.qvel[1]*math.cos(yaw));p['coupled_episode']=bool(episode);p['steering_motion_active']=bool(getattr(v.adapter,'_steering_motion_active',False));return p

def complete_stop(x,engine,origin):
 ss,uu=engine.simulate(origin,[(0.,0.,2200,0)]);p=dict(x,goal=ss[-1,:2].tolist());proof,rr=final_gate(p,ss,uu,[(0.,0.,2200,0)]);return proof,ss,uu,rr

def execute(v,setup,original,end,evidence,out,packet_fn,output):
 root=v.count
 try:
  answer=normal.execute(v,setup,original,end,evidence,out,packet_fn,output);dump(out/'RECOVERY_BRANCH.json',{'mode':'LEGACY_NORMAL','normal_science_unchanged':True});return answer
 except AssertionError as error:
  label=error.args[0] if error.args else None;label=label[0]if isinstance(label,tuple)and label else label
  if v.count!=root or label not in ['NO_LIVE_COMPLETE_DYNAMIC_REFERENCE','LIVE_COMPLETE_STATIC_REFERENCE_REQUIRED']:raise
  dump(out/'LEGACY_FUNCTIONAL_REJECTION.json',{'reason':str(error),'native':v.count,'physical_steps_during_rejected_proposal':0})
 import mujoco as mj
 from kernel import load
 plan=load('night_causal_smac_proposal',C/'night_planner.py').plan
 bind(v,Adapter,mj);episode=False;anchor=None;origin=v.count;source=evidence.source(v);p=extended_packet(v,packet_fn,episode);goal=original['goal'];x={'setup':setup,'packet':p,'source':source,'goal':goal,'goal_yaw':setup['case']['yaw']};engine=Engine(setup);journal=[];blocks=[];failure=None;actual_native_start=v.count;maximum=np.zeros(3);mode_envelopes=[];current_mode=False
 certificates=out/'coupled_certificates';certificates.mkdir();journal_stream=(out/'MODE_JOURNAL.jsonl').open('x',buffering=131072)
 config=json.loads((Path(output)/'CONFIG.json').read_text());candidate=config['active_candidate'];radius=float(candidate['radius_extra']);block_size=int(candidate['block_native']);x['mode_reserve']=candidate['mode_reserve'];dump(out/'RECOVERY_BRANCH.json',{'mode':'COUPLED_COMPLETE','candidate':candidate,'original_physical_root':root,'geometric_contract':'Smac soft guidance; complete propagated executable source is hard reference'});dump(out/'COUPLED_ENTRY.json',x)
 def publish_counts():
  COUNTS['cpp_native']=engine.native;COUNTS['cpp_partial_work_unknown']=bool(getattr(engine,'in_call',False));dump(out/'COUPLED_COUNTS.json',COUNTS)
 def applied(req,mode,target,expected,index,phase):
  nonlocal episode,anchor,current_mode,maximum
  assert time.time()<end-120,'REPLAY_RESERVE'
  if mode and not current_mode:
   body=v.body();enc=v.steering_sample();assert abs(body[3])<=.003 and abs(body[4])<=.003 and abs(enc[2:]).max()<=.015,'ACTUAL_MODE_ENTRY_NOT_REST'
   anchor=np.array(body[:3]);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(anchor[None,:]);low=float(min(a[0],b[0]))-.02-math.hypot(.44,.375)*.1
   if low<REQUIRED:raise SourceRefusal('ACTUAL_MODE_ENVELOPE_REFUSED')
   mode_envelopes.append({'native':v.count,'anchor':anchor.tolist(),'raw_envelope_lower':low});dump(out/'MODE_ENVELOPES.json',mode_envelopes)
  if abs(req[0])>=.005:anchor=None
  row={'before_native':v.count,'parked':bool(mode),'target':float(target),'last_ctrl':v.adapter.last.tolist(),'integral':float(v.adapter.integral),'episode':episode,'active':bool(getattr(v.adapter,'_steering_motion_active',False)),'index':index,'phase':phase}
  v.adapter.parked_target=float(target)if mode else None
  v.step(*req);journal.append(row);journal_stream.write(json.dumps(row,separators=(',',':'))+'\n')
  if mode:episode=True
  if abs(req[0])>=.005:episode=False
  current_mode=bool(mode);b=np.array(v.body());angle=b[2]-expected[2];e=np.array([np.linalg.norm(b[:2]-expected[:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(kernel.virtual(v.steering_sample()[:2])-expected[6])]);maximum=np.maximum(maximum,e);assert np.all(e<=[.04,.035,.015]),'ACTUAL_SOURCE_TRACKING_ANOMALY';lateral=-v.d.qvel[0]*math.sin(b[2])+v.d.qvel[1]*math.cos(b[2]);assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(lateral)<=.03,'ACTUAL_BODY_CAP'
  if anchor is not None:
   assert np.linalg.norm(b[:2]-anchor[:2])<=.02 and abs(math.atan2(math.sin(b[2]-anchor[2]),math.cos(b[2]-anchor[2])))<=.1,'ACTUAL_MODE_ENVELOPE_ANOMALY'
  if mode:assert abs(b[3])<=.01 and np.max(abs(v.d.ctrl[v.adapter.commands.ids[2:]]))<=1e-10,'ACTUAL_COUPLED_MODE_ANOMALY'
  if v.count%5==0:evidence.update(v.scan())
 try:
  proposal=plan(x,out/'smac_proposal',radius)
  if not proposal['passed']:raise SourceRefusal('SMAC_NO_PATH')
  result=solve(x,proposal['path'],proposal['gear']);dump(out/'SOURCE_OPTIMIZATION.json',{k:z for k,z in result.items()if k not in ['states','controls','requests']})
  if not result['passed']:raise SourceRefusal('COMPLETE_PROPAGATED_SOURCE_REFUSED')
  ps,pu,*_=python_replay(setup,initial(p),result['rows']);COUNTS['python_native']+=len(pu);assert max(float(abs(ps-result['states']).max()),float(abs(pu-result['controls']).max()))<=1e-8,'INITIAL_SOURCE_MODEL_MISMATCH';np.savez_compressed(out/'COUPLED_INITIAL_SOURCE.npz',states=result['states'],controls=result['controls'],requests=result['requests']);schedule=result['rows'];dump(out/'COUPLED_SCHEDULE.json',schedule);total=len(result['requests']);offset=0
  while offset<total:
   packet=extended_packet(v,packet_fn,episode);current=dict(x,packet=packet);suffix=remaining_rows(schedule,offset);ss,uu=engine.simulate(initial(packet),suffix);proof,rr=final_gate(current,ss,uu,suffix)
   # An active steering episode retains its original real anchor, not a new one.
   if suffix[0][3]and packet['steering_motion_active']:
    assert anchor is not None
    k=int(suffix[0][2]);phase=ss[:k+1];a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(anchor[None,:]);low=float(min(a[0],b[0]))-.02-math.hypot(.44,.375)*.1;inside=bool(np.linalg.norm(phase[:,:2]-anchor[:2],axis=1).max()<=.02 and abs(np.arctan2(np.sin(phase[:,2]-anchor[2]),np.cos(phase[:,2]-anchor[2]))).max()<=.1)
    proof['checks']['coupled_mode_envelopes']=bool(low>=REQUIRED and inside and all(r['passed']for r in proof['mode_envelopes'][1:]));proof['passed']=bool(all(proof['checks'].values()))
   if not proof['passed']:raise SourceRefusal('ACTUAL_FULL_SUFFIX_REFUSED')
   prefix=2200 if offset==total-2200 else min(block_size,total-2200-offset);assert prefix>0
   prefix_schedule=front_rows(suffix,prefix);pred,controls,memory,episodes,active=python_replay(setup,initial(packet),prefix_schedule);COUNTS['python_native']+=prefix;assert max(float(abs(pred-ss[:prefix+1]).max()),float(abs(controls-uu[:prefix]).max()))<=1e-8,'PREFIX_ACCELERATOR_MISMATCH'
   if prefix!=2200:
    future=forecast_packet(packet,pred[-1],memory[-1],prefix);future.update(body_lateral=float(pred[-1,4]),coupled_episode=bool(episodes[-1]),steering_motion_active=bool(active[-1]));backup_origin={'state':pred[-1].copy(),'last_ctrl':memory[-1,:4].copy(),'integral':float(memory[-1,4]),'coupled_episode':bool(episodes[-1]),'steering_motion_active':bool(active[-1])};backup,_,_,_=complete_stop(dict(x,packet=future),engine,backup_origin)
    if not backup['passed']:raise SourceRefusal('COMPLETE_PREFIX_BACKUP_REFUSED')
   else:backup={'passed':True,'terminal_full_stop':True}
   record={'number':len(blocks),'start_native':v.count,'offset':offset,'packet':packet,'prefix':prefix,'proof':proof,'backup':backup,'executed':0,'cpp_states_sha256':digest(ss),'cpp_controls_sha256':digest(uu)};blocks.append(record);dump(certificates/(str(record['number'])+'.json'),record);i=0
   for target,speed,ticks,mode in prefix_schedule:
    for _ in range(int(ticks)):
     applied(rr[i],mode,target,ss[i+1],offset+i,'source');i+=1;record['executed']+=1
   offset+=prefix;dump(certificates/(str(record['number'])+'.json'),record);journal_stream.flush()
   if len(blocks)%125==0 or offset==total:publish_counts();dump(out/'PARTIAL.json',{'phase':'COUPLED_COMPLETE_SOURCE','native':v.count,'offset':offset,'total':total,'blocks':len(blocks)})
  assert np.linalg.norm(v.body()[3:])<=.03,'ACTUAL_TERMINAL_REST'
 except SourceRefusal as e:
  failure=str(e);packet=extended_packet(v,packet_fn,episode);stop,ss,uu,rr=complete_stop(dict(x,packet=packet),engine,initial(packet));dump(out/'FUNCTIONAL_REFUSAL.json',{'reason':failure,'native':v.count,'stop_proof':stop,'packet':packet});assert stop['passed'],'FAILURE_STOP_SAFETY_REFUSED';begin=v.count
  for i,r in enumerate(rr):applied(r,False,0.,ss[i+1],None,'failure_stop')
  dump(out/'FUNCTIONAL_FAILURE_STOP.json',{'passed':bool(np.linalg.norm(v.body()[3:])<=.03),'begin':begin,'end':v.count,'native':2200});assert np.linalg.norm(v.body()[3:])<=.03,'FUNCTIONAL_FAILURE_NOT_STOPPED'
 finally:
  journal_stream.flush();journal_stream.close()
  for record in blocks:dump(certificates/(str(record['number'])+'.json'),record)
  dump(out/'MODE_JOURNAL.json',journal);dump(out/'COUPLED_BLOCKS.json',blocks);publish_counts()
 if failure:raise SourceRefusal(failure)
 return {'passed':True,'root_native':origin,'source_native_tick':source['source_native_tick'],'recovery_native':v.count-origin,'complete_stop_native':2200,'maximum_local_tracking':maximum.tolist(),'candidate':candidate,'mode':'COUPLED_COMPLETE'}
