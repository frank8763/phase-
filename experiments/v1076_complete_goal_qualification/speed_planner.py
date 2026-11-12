"""Bounded analytical proposal; full original Python regeneration is mandatory."""
import ctypes,hashlib,json,math,subprocess,time,os,fcntl
from pathlib import Path
import numpy as np
from kernel import R,C,O,PARAMETERS,initial,public_setup,predict,checks,Geometry,ref,REQUIRED
from time_geometry import interval_support
C=Path(__file__).resolve().parent;O=R/'runs/v1076_complete_goal_qualification'

def library():
 source=C/'speed_search.cpp';dependency=R/'experiments/v1046_retreat_entry_timed_route/fast_predict.cpp'
 digest=hashlib.sha256(source.read_bytes()+dependency.read_bytes()).hexdigest();cache=O/'analytical_cache';target=cache/(digest[:20]+'.so')
 if not target.is_file():
  assert not(O/'ROUND_WINDOW.json').exists(),'FROZEN_ANALYTICAL_BINARY_MISSING'
  cache.mkdir(exist_ok=True,parents=True)
  with (cache/'compiler.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   if not target.exists():
    temporary=cache/(digest[:20]+'.'+str(os.getpid())+'.tmp.so');subprocess.run(['g++','-std=c++17','-O3','-fPIC','-shared',str(source),'-o',str(temporary)],check=True,timeout=30);os.replace(temporary,target)
 lib=ctypes.CDLL(str(target));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
 lib.search.argtypes=[a,a,a,a,a,a,ctypes.c_int,a,ctypes.c_int,a,ctypes.c_int,ctypes.c_double,ctypes.c_double,a,ctypes.c_double,ctypes.c_int,a,ctypes.POINTER(ctypes.c_int),a];lib.search.restype=ctypes.c_int
 lib.static_pose.argtypes=[ctypes.c_double,ctypes.c_double,ctypes.c_double,a,ctypes.c_int,a,ctypes.c_int];lib.static_pose.restype=ctypes.c_double
 lib.stop_lower.argtypes=[a,a,a,a,a,a,ctypes.c_int,a,ctypes.c_int,ctypes.c_int];lib.stop_lower.restype=ctypes.c_double
 return lib

def construct(setup,packet,source,goal,wall_s=8.,max_expansions=200000,guidance_actions=None):
 setup=public_setup(setup);begun=time.monotonic();lib=library();origin=initial(packet);state=np.ascontiguousarray(origin['state'],float);memory=np.ascontiguousarray([*origin['last_ctrl'],origin['integral']],float)
 rect=np.ascontiguousarray(setup['known']['known_rectangles'],float);circles=np.ascontiguousarray(setup['known']['known_circles'],float);limits=np.ascontiguousarray(setup['limits'],float);rates=np.ascontiguousarray(setup['slew_per_second'],float);p=PARAMETERS;parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']],float)
 period=2*math.pi/.32;dt=.025;edges=np.arange(0,period,dt)if source is not None else np.empty(0);support=interval_support(source['periodic']['vertices'],edges-.075,edges+dt+.075)if source is not None else np.zeros((1,16));support=np.ascontiguousarray(np.vstack([support,support.max(axis=0)]));actions=np.zeros((1000,3));count=ctypes.c_int();stats=np.zeros(5);goal=np.ascontiguousarray(goal,float)
 from goal_guide import reference
 guide=reference(setup,packet,goal,guidance_actions);a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');lib.set_reference.argtypes=[a,ctypes.c_int];lib.set_reference.restype=None;lib.set_reference(guide,len(guide))
 code=lib.search(state,memory,limits,rates,parameters,rect,len(rect),circles,len(circles),support,len(edges),dt,packet['sim_time'],goal,wall_s,max_expansions,actions,ctypes.byref(count),stats)
 result=dict(passed=False,models=0,integrations=0,status='ANALYTICAL_SEARCH_WALL_EXCEPTION'if code==5 else'ANALYTICAL_SEARCH_CAP'if code else'UNVERIFIED_COMPLETE_CANDIDATE',terminated_by_wall=code==5,expanded=int(stats[0]),search_wall_s=float(stats[1]),best_goal_distance_m=float(stats[2]),generated=int(stats[3]),rejected=int(stats[4]),proposal_only=True,original_goal=goal.tolist(),required_raw_m=REQUIRED,source_native_tick=source['source_native_tick']if source is not None else None,root_native_tick=packet['native_tick'])
 if code not in [0,4]:return result
 targets=np.linspace(-.42722137342572125,.42722137342572125,5);profile=[]
 for action,ticks,target_value in actions[:count.value]:
  action=int(action);ticks=int(ticks)
  row=dict(kind='wait',gear=0,target=0.,ticks=ticks)if action==10 else dict(kind='move',gear=1 if action<5 else-1,target=float(target_value)if action in [11,12]else float(targets[action%5]),speed=.08 if action<5 else-.03,ticks=ticks)
  if action in [11,12]:row=dict(kind='move',gear=1 if action==11 else-1,target=float(target_value),speed=.08 if action==11 else-.03,ticks=ticks)
  if action>=13:row=dict(kind='move',gear=1,target=float(target_value),speed=.03,ticks=ticks)
  if profile and all(profile[-1].get(k)==row.get(k)for k in ['kind','gear','target','speed']):profile[-1]['ticks']+=ticks
  else:profile.append(row)
 states,ctrl,requests,mem=predict(setup,packet,profile,tail=True)
 if source is not None:minimum=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(states)
 else:minimum=float(ref._old.Geometry(setup['known'],None).clearances(states[:,:3])[0].min())
 cc,upper=checks(states,ctrl,requests,packet,setup,goal,minimum,REQUIRED);a,b=ref._old.Geometry(setup['known'],source['periodic']if source is not None else None).clearances(states[-1:,:3]);cc['terminal_full_cycle_hold']=bool(min(a[0],b[0])>=REQUIRED)
 cc['all_gear_switches_stopped']=all(i>0 and profile[i-1]['kind']=='wait'and profile[i-1]['ticks']>=200 for i,x in enumerate(profile)if x['kind']=='move'and i and x['gear']!=next((q['gear']for q in reversed(profile[:i])if q['kind']=='move'),x['gear']))
 goal_source=code==0;safety=dict(cc)
 if not goal_source:safety.pop('goal_upper');safety['terminal_additional_observation_reserve']=bool(min(a[0],b[0])>=REQUIRED+.02)
 passed=all(safety.values());result.update(passed=bool(passed),status=('ORIGINAL_PYTHON_COMPLETE_GOAL_SOURCE_PASS'if goal_source else'ORIGINAL_PYTHON_FINITE_PROGRESS_SOURCE_NOT_ARRIVAL')if passed else'ORIGINAL_PYTHON_SOURCE_REJECTED',functional_goal_source=goal_source,finite_progress_never_counts_as_arrival=not goal_source,actions=profile+[dict(kind='wait',gear=0,target=0.,ticks=200)],checks=safety,original_goal_profile_checks=cc,minimum_raw_m=minimum,terminal_goal_upper_m=upper,analytical_native=len(requests),state_path=states.tolist(),predicted_actuator_controls=ctrl.tolist(),planned_body_requests=requests.tolist(),wall_s=time.monotonic()-begun)
 return result
