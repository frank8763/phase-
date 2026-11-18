"""Saved-array reconstruction of every nominal stop and executed backup."""
from pathlib import Path
import json,time,math,sys,gzip,importlib.util
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import original
import stop_certificates as stops
q=original.q;np=q.np
read=lambda p:json.loads(Path(p).read_text())
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def verify_selected(out,deadline):
 out=Path(out);x=read(out/'LIVE_OBSERVER_INPUT.json');chosen=read(out/'LIVE_OBSERVER_SELECTION.json')
 with np.load(out/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 with np.load(out/'LIVE_OBSERVER_REFERENCE.npz')as z:ss=z['states'].copy();mm=z['memory'].copy()
 records=chosen['complete_stop_qualification']['records'];assert chosen['complete_stop_qualification']['passed'] and chosen['selected']['complete_stops_passed']
 flags=stops.flags_before(chosen['rows']);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);g=q.Geometry(x,table);offset=0;minimum=float('inf')
 for rec in records:
  assert time.monotonic()<deadline and rec['offset']==offset
  suffix=original.remaining_rows(chosen['rows'],offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));assert rec['prefix']==n
  block=original.front(suffix,n);p=stops.forecast(x,ss[offset],mm[offset],offset);p.update({k:v for k,v in flags[offset].items()if k!='steering_load_episode'})
  origin=dict(state=ss[offset],last_ctrl=mm[offset,:4],integral=float(mm[offset,4]),**flags[offset])
  for key,schedule in [('current',[(0.,0.,2200,0)]),('prospective',[*block,(0.,0.,2200,0)])]:
   pred,u,_=engine.simulate(origin,schedule);goal=pred[-1,:3].tolist();proof,_=g.final(dict(x,packet=p,goal=goal[:2],safe_terminal_pose=goal),pred,u,schedule)
   assert proof['passed'] and rec[key+'_passed'] and abs(proof['minimum_raw_m']-rec[key+'_raw'])<=1e-8
   minimum=min(minimum,proof['minimum_raw_m'])
  offset+=n
 assert offset==len(ss)-1 and abs(minimum-chosen['selected']['minimum_stop_raw_m'])<=1e-8
 return dict(passed=True,complete_stop_certificates=len(records),minimum_stop_raw_m=minimum,analytical_cpp_native=engine.native,models=0,new_mujoco_native=0)

def verify_backup(out,deadline):
 out=Path(out);parent=load('v1219_backup_native_helpers',R/'experiments/v1204_goal_audit_worker/native_audit.py');setup=read(out/'physics/SETUP.json')
 with np.load(out/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
 p0=read(out/'CANONICAL_INITIAL_PACKET.json');states=np.vstack([q.initial(p0)['state'],parent.projection(trace['qpos'],trace['qvel'],setup)])
 with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 x=read(out/'LIVE_OBSERVER_INPUT.json');start=x['packet']['native_tick'];table=parent.table_check(out,'LIVE_OBSERVER',x,sensors);g=q.Geometry(x,table);chosen=read(out/'LIVE_OBSERVER_SELECTION.json');rows=chosen['rows'];engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);certs=read(out/'LIVE_OBSERVER_CERTIFICATES.json');flags=stops.flags_before(rows);offset=0
 assert abs(q.initial(x['packet'])['state']-states[start]).max()<=1e-8
 with np.load(out/'LIVE_OBSERVER_REFERENCE.npz')as z:ref=z['states'].copy()
 commands=np.asarray(read(out/'physics/BODY_COMMANDS.json'));pred_stop=None
 for index,c in enumerate(certs):
  assert time.monotonic()<deadline and c['offset']==offset and c['native']==start+offset
  p=c['packet'];assert abs(q.initial(p)['state']-states[start+offset]).max()<=1e-8
  assert c['steering_load_episode']==flags[offset]['steering_load_episode'] and p['coupled_episode']==flags[offset]['coupled_episode'] and p['steering_motion_active']==flags[offset]['steering_motion_active']
  suffix=original.remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));assert n==c['prefix']
  block=original.front(suffix,n);proof,pred=stops.prove(engine,g,x,p,dict(q.initial(p),steering_load_episode=c['steering_load_episode']),block)
  for key,pr in zip(['current','prospective'],proof):assert pr['passed']==c[key]['passed'] and pr['states_sha256']==c[key]['states_sha256'] and pr['controls_sha256']==c[key]['controls_sha256']
  assert proof[0]['passed']
  if index==len(certs)-1:
   assert not proof[1]['passed'];pred_stop=pred[0];break
  assert proof[1]['passed'];d=states[start+offset:start+offset+n+1]-pred[1][:n+1];assert(np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all();offset+=n
 assert pred_stop is not None and len(states)-1==start+offset+2200
 planned=np.array([[v,0. if mode or v==0. else v*math.tan(t)/.6,0.]for t,v,n,mode in rows for _ in range(int(n))])
 assert abs(planned[:offset]-commands[start:start+offset][:,[1,2,5]]).max()<=1e-12
 assert np.array_equal(commands[start+offset:][:,[1,2,5]],np.zeros((2200,3)))
 d=states[start:start+offset+1]-ref[:offset+1];assert(np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all()
 d=states[start+offset:]-pred_stop;assert(np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]<=[.04,.035,.015]).all()
 final=read(out/'ACTUAL_FINAL_PACKET.json');assert original.previous.stopped(final)
 record=read(out/'OBSERVER_EXECUTED_STOP.json');assert record['complete'] and record['native']==2200 and record['entry_native']==start+offset
 with np.load(out/'OBSERVER_EXECUTED_STOP.npz')as z:assert abs(z['actual']-states[start+offset:]).max()<=1e-8 and abs(z['expected']-pred_stop).max()<=1e-8
 return dict(passed=True,functional_passed=False,complete_stop_native=2200,observer_prefix_native=offset,analytical_cpp_native=engine.native,models=0,new_mujoco_native=0)
