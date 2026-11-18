"""Independent saved physical/control/refresh audit; constructs no model."""
from common_short import *
import gzip,math,signal
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import Adapter,ref,REQUIRED
import kernel
from source import Engine,initial
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from fast_cycle import certify
from refresh import causal_packets

def audit():
 out=Path(json.loads((C/'TASK.json').read_text())['output']);r=json.loads((out/'RESULT.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());data=np.load(out/'physics/NATIVE_TRACE.npz');old=np.load(R/'runs/v858_nav2_verified/v1144/observation_main/physics/NATIVE_TRACE.npz');journal=json.loads((out/'MODE_JOURNAL.json').read_text());bundle=json.loads((out/'REFRESH_CERTIFICATES.json').read_text());packet=bundle['packet'];source=json.loads((out/'ACTUAL_CAUSAL_SOURCE.json').read_text());n=len(data['qpos']);base=32515
 source_scans=json.loads(gzip.open(out/'physics/SENSORS.json.gz','rt').read());prefix=[p for p in source_scans if p['native_tick']<=base]
 clean,duplicates=causal_packets(prefix,packet)
 causal=load('short_independent_causal',R/'experiments/v1024_full_route_execution/causal.py');norm=load('short_independent_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
 evidence=causal.Evidence(setup['known']);evidence.periodic=norm.PeriodicSupport()
 for row in clean:evidence.update(row)
 import types
 rebuilt=evidence.source(types.SimpleNamespace(d=types.SimpleNamespace(time=packet['sim_time'])))
 assert all(rebuilt[k]==source[k]for k in ['source_native_tick','source_age_s','periodic']),'OBSERVATION_SOURCE_RECONSTRUCTION'
 maximum=max(float(abs(data[k][:base]-old[k][:base]).max())if data[k][:base].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])
 q=data['qpos'];v=data['qvel'];quat=q[:,3:7];yaw=np.arctan2(2*(quat[:,0]*quat[:,3]+quat[:,1]*quat[:,2]),1-2*(quat[:,2]**2+quat[:,3]**2));poses=np.c_[q[:,:2],yaw];ctrl=data['ctrl'][:,setup['actuator_ids']];speed=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);lateral=-v[:,0]*np.sin(yaw)+v[:,1]*np.cos(yaw)
 adapter=kernel.Predictor(setup,dict(state=[0.]*8,last_ctrl=packet['controller_memory']['last_ctrl'],integral=packet['controller_memory']['integral'],virtual_rate=.6),kernel.PARAMETERS).adapter;adapter.__class__=Adapter;adapter.virtual_rate=.6
 commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());control_error=0.;memory=True;requests=True
 for i,row in enumerate(journal):
  k=base+i;enc=np.r_[q[k-1,setup['steering_qpos_addresses']],v[k-1,setup['steering_qvel_addresses']]];adapter.encoders=lambda enc=enc:enc.copy();adapter.parked_target=None;memory&=bool(np.max(abs(adapter.last-row['last_ctrl']))<=1e-10 and abs(adapter.integral-row['integral'])<=1e-10)
  _,vr,wr,bv,bw,stale=commands[k];u=adapter.compute(vr,wr,bv,bw,bool(stale));control_error=max(control_error,float(abs(u-ctrl[k]).max()));requests&=bool(row['native']==k and row['component_index']==i and vr==row['speed'] and abs(wr-(0. if vr==0 else vr*math.tan(row['target'])/.6))<=1e-12)
 limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01;static=ref._old.Geometry(setup['known'],None).clearances(poses)[0]
 engine=Engine(setup);proofs={}
 schedule=[]
 for row in journal:
  entry=(row['target'],row['speed'],1,0)
  if schedule and schedule[-1][:2]==entry[:2]:a,b,c,d=schedule[-1];schedule[-1]=(a,b,c+1,d)
  else:schedule.append(entry)
 for name,rows in [('current',[(0.,0.,2200,0)]),('prospective',schedule)]:
  states,controls=engine.simulate(initial(packet),rows);proof=certify(dict(setup=setup,packet=packet,source=source,goal=states[-1,:2].tolist(),safe_terminal_pose=states[-1,:3].tolist()),states,controls,rows);original=bundle['proofs'][name]
  assert proof==original,'FULL_CERTIFICATE_RECONSTRUCTION';proofs[name]=proof
 checks=dict(history_exact=maximum<=1e-8,complete_native_lengths=n==34723==len(commands)and len(journal)==2208,actual_packet_native=packet['native_tick']==32515,actual_measurement_source_exact=True,full_current_and_next_stop=all(p['passed']for p in proofs.values()),all_control_reconstruction=control_error<=1e-10 and memory and requests,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),actual_static_body=float(static.min())>=.15-1e-8,actual_clearance=float(data['clearance'].min())>=.15-1e-8,self_containment=float(data['self_margin'].min())>=-1e-10,bad_contacts_zero=r['physical']['bad_contacts']==0,body_caps=bool((abs(speed)<=.13).all()and(abs(v[:,5])<=.16).all()and(abs(lateral)<=.03).all()),complete2200tail=len(journal)==2208 and all(row['speed']==row['target']==0 for row in journal[-2200:]),actual_stopped=bool(np.linalg.norm(v[-50:,:2],axis=1).max()<=.003 and abs(v[-50:,5]).max()<=.003 and abs(v[-50:,setup['steering_qvel_addresses']]).max()<=.015),actual_terminal=r['terminal_position_error_m']<=.025 and r['terminal_yaw_error_rad']<=.1 and r['actual_full_cycle_raw_m']>=REQUIRED,complete_own_replay=r['replay']['passed']and r['own_replay_native']==n,source_unchanged=source_ok())
 result=dict(passed=bool(all(checks.values())),checks=checks,history_max_error=maximum,control_max_error=control_error,analytical_cpp_native=engine.native,models=0,physical_native=0,new24_executed=False)
 dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);print(encode(result));return result

if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SAVED_AUDIT60')));signal.alarm(60)
 result=audit();sys.exit(0 if result['passed']else 1)
