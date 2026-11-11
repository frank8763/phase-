"""Full forecast, publication clock and measurement faults for a long suffix."""
import copy,importlib.abc,json,sys,time,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from atomic import allocate,publish
from capture import capture
pin_threads();folder=O/'generic_source_qualification';x=json.loads((folder/'INPUT.json').read_text());proposal=json.loads((folder/'RESULT.json').read_text());assert proposal['passed'];buffers=allocate(proposal)
def fresh_packet(original,full_s,full_m):
 state=full_s[800];memory=full_m[800];p=copy.deepcopy(original);k=math.tan(state[6])/.6;kd=(1+math.tan(state[6])**2)/.6*state[7];q=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))];rates=(.6*kd/(np.array([1-.27*k,1+.27*k])**2+(.6*k)**2)).tolist();now=time.monotonic();p.update(body=[*state[:4],state[5]],native_tick=original['native_tick']+800,sim_time=original['sim_time']+8.,body_measured_at=now,sent_at=now);p['steering'].update(position=q,velocity=rates,native_tick=p['native_tick'],measured_at=now);p['controller_memory']=dict(last_ctrl=memory[:4].tolist(),integral=float(memory[4]));return p
s,u,r,m=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=800)],tail=False);packet=fresh_packet(x['packet'],s,m);source=copy.deepcopy(x['source']);source.update(source_native_tick=packet['native_tick'],source_age_s=0.);view=publish(buffers,packet,source,packet['sent_at']);record=view.record();assert record['pre_adoption_hold_native']==800;whole,controls,requests,mem=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=800)]+record['actions'],tail=False);ss=whole[800:];uu=controls[800:];rr=requests[800:];errors=[float(abs(ss-record['state_path']).max()),float(abs(uu-record['predicted_actuator_controls']).max()),float(abs(rr-record['planned_body_requests']).max())];assert max(errors)==0.;minimum=Geometry(x['setup']['known'],source['periodic'],packet['sim_time']).complete(ss);cc,upper=checks(ss,uu,rr,dict(controller_memory=packet['controller_memory']),x['setup'],np.array(x['goal']),minimum,REQUIRED);assert all(cc.values());negative=[]
for name in ['wrong_native','wrong_time','removed_clock_kind','changed_wait']:
 p=fresh_packet(x['packet'],s,m)
 try:
  if name=='wrong_native':p['native_tick']+=1;p['steering']['native_tick']+=1;publish(buffers,p,source,p['sent_at'])
  elif name=='wrong_time':p['sim_time']+=.001;publish(buffers,p,source,p['sent_at'])
  else:
   bad=copy.deepcopy(proposal)
   if name=='removed_clock_kind':bad.pop('publication_clock_kind')
   else:bad['fixed_launch_wait']+=1
   allocate(bad)
 except AssertionError:negative.append(name)
 else:raise AssertionError('CLOCK_MUTATION_ACCEPTED '+name)
class Vehicle:
 count=packet['native_tick']
class Evidence:
 def source(self,v):return copy.deepcopy(source)
calls=[0]
def first_stale(v,discovered):
 p=fresh_packet(x['packet'],s,m);calls[0]+=1
 if calls[0]==1:p['sent_at']-=.07;p['body_measured_at']-=.07;p['steering']['measured_at']-=.07
 return p
captured=capture(buffers,Vehicle(),Evidence(),first_stale,time.time()+2);assert calls[0]==2 and len(captured.attempts)==2 and not captured.attempts[0]['accepted']and captured.attempts[1]['accepted'];dump(O/'FIXED_CLOCK_PUBLICATION_AUDIT.json',dict(passed=True,original_python_full_hold_wait_and_suffix_reconstruction_error=errors,pre_adoption_zero_hold_native=800,all_geometry_goal_control_checks=cc,minimum_raw_m=minimum,goal_upper_m=upper,negative_cases=negative,one_stale_measurement_reacquired_without_native_advance=True,models=0,integrations=0,synthetic_NS_source_only=True));print(json.dumps(dict(passed=True,errors=errors,negative_cases=negative,models=0,integrations=0)))
