"""Static topology proposal + timed launch, all original-Python checks required."""
import ctypes,math,time
import numpy as np
from kernel import predict,checks,Geometry,ref,REQUIRED
from planner import interval_support
from static_planner import construct,library

def prepare(x,max_expansions=5000):
 from recovery_source import forecast_packet
 started=time.monotonic();s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);p=forecast_packet(x['packet'],s[-1],m[-1],1001)
 candidate=construct(x['setup'],p,None,x['goal'],wall_s=8.,max_expansions=max_expansions)
 assert candidate['passed']and candidate['functional_goal_source'],'NO_STATIC_COMPLETE_GOAL_PROPOSAL'
 profile=np.ascontiguousarray(np.asarray(candidate['state_path'])[:,:3]);g=Geometry(x['setup']['known'],x['source']['periodic'],p['sim_time']);support=np.ascontiguousarray(np.vstack([g.support,g.support.max(axis=0)]));period=2*math.pi/.32;stride=10;slots=math.ceil(period/(stride*.01));bounds=np.zeros(slots);lib=library();arr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');lib.profile_launch_bounds.argtypes=[arr,ctypes.c_int,arr,ctypes.c_int,ctypes.c_double,ctypes.c_double,arr,ctypes.c_int,ctypes.c_int];lib.profile_launch_bounds.restype=ctypes.c_int;assert lib.profile_launch_bounds(profile,len(profile),support,len(g.support),g.bin,p['sim_time'],bounds,slots,stride)==0
 eligible=np.flatnonzero(bounds>=REQUIRED+1e-7);assert len(eligible),'NO_CERTIFIED_LAUNCH_FOR_STATIC_PROFILE';selected=int(eligible[np.argmax(bounds[eligible])]);wait=1+selected*stride
 joined=[dict(kind='wait',gear=0,target=0.,ticks=800),dict(kind='wait',gear=0,target=0.,ticks=200),dict(kind='wait',gear=0,target=0.,ticks=wait)]+candidate['actions'];full_s,full_u,full_r,full_m=predict(x['setup'],x['packet'],joined,tail=False);ss,uu,rr=full_s[800:],full_u[800:],full_r[800:];minimum=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']+8).complete(ss);memory=dict(last_ctrl=full_m[800,:4].tolist(),integral=float(full_m[800,4]));cc,goal=checks(ss,uu,rr,dict(controller_memory=memory),x['setup'],np.asarray(x['goal']),minimum,REQUIRED);assert all(cc.values()),'FULL_ORIGINAL_PYTHON_REJECTED'
 a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:200+wait+1,:3]);assert min(a.min(),b.min())>=REQUIRED+1e-7,'PARKED_WAIT_NOT_FULL_CYCLE_SAFE';a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[-1:,:3]);assert min(a[0],b[0])>=REQUIRED,'GOAL_HOLD_NOT_FULL_CYCLE_SAFE'
 return dict(passed=True,functional_goal_source=True,goal_upper_m=goal,minimum_raw_m=minimum,wait_native=wait,static_expanded=candidate['expanded'],launch_candidates=slots,eligible_launches=len(eligible),checks=cc,actions=joined,original_python_states=full_s.tolist(),original_python_controls=full_u.tolist(),original_python_requests=full_r.tolist(),wall_s=time.monotonic()-started,models=0,integrations=0)
