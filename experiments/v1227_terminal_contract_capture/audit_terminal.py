"""Independent C++ reconstruction of a complete terminal decision and tail."""
from pathlib import Path
import importlib.util,copy,sys,math,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import q,np
s=importlib.util.spec_from_file_location('v1227_terminal_endpoint',R/'experiments/v1198_control_space_connection/connection.py');conn=importlib.util.module_from_spec(s);sys.modules[s.name]=conn;s.loader.exec_module(conn)
def close(a,b,label):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape and(not a.size or abs(a-b).max()<=1e-8),label

def verify(x,table,origin,shadow_origin,offset,target,record,arrays):
 assert record['passed']and record['offset']==offset and record['terminal_position_contract_m']==.025 and record['extra_12mm_objective']is False
 for key in ['state','last_ctrl']:close(record['origin'][key],origin[key],'TERMINAL_CURRENT_'+key);close(record['shadow_origin'][key],shadow_origin[key],'TERMINAL_CARRIED_SHADOW_'+key)
 assert abs(record['origin']['integral']-origin['integral'])<=1e-8 and abs(record['shadow_origin']['integral']-shadow_origin['integral'])<=1e-8
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);current=copy.deepcopy(origin);ss=[np.asarray(current['state'])];uu=[];mm=[np.r_[current['last_ctrl'],current['integral']]];rr=[];capture=0
 def apply(v,w,n):
  nonlocal current
  a,u,m=engine.simulate(current,[q.accelerator.row(float(v),float(w))]*n)
  ss.extend(a[1:]);uu.extend(u);mm.extend(m[1:]);rr.extend([[float(v),float(w),0.]]*n);current=conn.endpoint(current,a,m,v>=.005)
 for _ in range(600):
  if np.linalg.norm(current['state'][:2]-target[:2])<=.025:break
  v,w,status=q.capture.request(current['state'],target);assert status=='CAPTURING';apply(v,w,1);capture+=1
 else:raise AssertionError('AUDIT_TERMINAL_CAPTURE_CAP')
 apply(0.,0.,2200);ss=np.asarray(ss);uu=np.asarray(uu);mm=np.asarray(mm);rr=np.asarray(rr)
 sh,_,_=engine.simulate(shadow_origin,[q.accelerator.row(float(v),float(w))for v,w,_ in rr])
 for key,value in [('states',ss),('shadow',sh),('controls',uu),('memory',mm),('requests',rr)]:close(arrays[key],value,'TERMINAL_REBUILD_'+key)
 local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=np.asarray(origin['last_ctrl']).tolist();geometry=conn.OffsetGeometry(q.Geometry(x,table),offset)
 proof=q.proof(geometry,local,ss,uu,rr,mm);sp=q.proof(geometry,local,sh,uu,rr,mm);assert proof['passed']and sp['passed'],'AUDIT_TERMINAL_GEOMETRY'
 for actual,expected in [(record['proof'],proof),(record['shadow_proof'],sp)]:
  assert actual['checks']==expected['checks']
  for k in ['minimum_raw_m','terminal_cycle_raw_m','goal_upper_m']:assert abs(actual[k]-expected[k])<=1e-8
 d=ss-sh;response=np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])];assert(response<=[.04,.035,.015]).all()
 d=ss[1:,:3]-target[:3];pose=np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2])))];assert(pose<=[.04,.035]).all()
 assert np.linalg.norm(ss[-1,:2]-target[:2])<=.025 and capture==record['capture_native']and len(uu)==record['native']
 close(record['maximum_response_error'],response[1:].max(0),'TERMINAL_RESPONSE_MAX');close(record['maximum_reference_error'],pose.max(0),'TERMINAL_POSE_MAX')
 return dict(passed=True,models=0,new_mujoco_native=0,complete_stop_native=2200,capture_native=capture,final_position_error_m=float(np.linalg.norm(ss[-1,:2]-target[:2])),maximum_yaw_error_rad=float(pose[:,1].max()),analytical_cpp_native=engine.native)
