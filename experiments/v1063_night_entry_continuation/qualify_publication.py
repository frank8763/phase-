"""Production parked executor with bounded delay faults; no MuJoCo imports."""
import copy,json,math,sys,time,tempfile,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1063_night_entry_continuation_20261111';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import Predictor,initial,PARAMETERS,load,dump,pin_threads
from atomic import allocate
sys.path.insert(0,str(C))
from capture import capture
new=load('v1060_software_executor',C/'execute.py');old=load('v1060_original_executor',R/'experiments/v1058_fresh_repeat_entry/execute.py');pin_threads();x=json.loads((R/'runs/v1061_three_route_readiness/dependencies/WE_MEASURED_INPUT.json').read_text());original=dict(actions=json.loads((C/'RECOVERY_WARM_SEED.json').read_text())['actions'],goal=x['goal']);fixtures=R/'runs/v1061_three_route_readiness/dependencies/software_producers';proposals=[json.loads((p/'RESULT.json').read_text())for p in sorted(fixtures.iterdir())if p.is_dir()];publication_ticks={p['packet']['native_tick']+800 for p in proposals}
import numpy as np
class Plant:
 def __init__(self):self.p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);self.count=23640;self.adapter=self.p.adapter;self.states=[];self.controls=[];self.requests=[]
 def step(self,*request):s,u=self.p.step(*request);self.count+=1;self.states.append(s.copy());self.controls.append(u.copy());self.requests.append(request)
 def body(self):s=self.p.state;return [*s[:4],s[5]]
 def steering_sample(self):
  s=self.p.state;k=math.tan(s[6])/.6;kd=(1+math.tan(s[6])**2)/.6*s[7];front=np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]);rates=.6*kd/(np.array([1-.27*k,1+.27*k])**2+(.6*k)**2);return np.r_[front,rates]
 def scan(self):return dict(native_tick=self.count)
def packet(v,discovered):
 now=time.monotonic();enc=v.steering_sample();return dict(body=v.body(),native_tick=v.count,sim_time=x['packet']['sim_time']+(v.count-23640)*.01,body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=enc[:2].tolist(),velocity=enc[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)))
class Evidence:
 def __init__(self,delay=False):self.calls=0;self.delay=delay
 def update(self,scan):pass
 def source(self,v):
  self.calls+=1
  if self.delay and self.calls%2==0:time.sleep(.07)
  return dict(source_native_tick=v.count,source_age_s=0.,decision_at=time.monotonic(),periodic=copy.deepcopy(x['source']['periodic']))
class SavedProducer:
 def __init__(self,folder,payload):
  self.result=json.loads((fixtures/folder.name/'RESULT.json').read_text());assert np.max(abs(np.array(payload['packet']['body'])-self.result['packet']['body']))<=1e-8;folder.mkdir(parents=True,exist_ok=False)
 def finish(self):return self.result
 def close(self):pass
rows=[]
with tempfile.TemporaryDirectory(dir=O,prefix='pure_software_')as temp:
 v=Plant();root=Path(temp)/'baseline';root.mkdir();baseline=old.execute(v,x['setup'],original,time.time()+300,Evidence(),root,packet,job_class=SavedProducer,pace=False);saved=[np.array(v.states),np.array(v.controls),np.array(v.requests)]
 for name,delay,stale in [('same_numeric_path',False,False),('70ms_snapshot_before_packet',True,False),('one_stale_packet_per_epoch',False,True)]:
  v=Plant();counts={}
  def observed(v,discovered):
   p=packet(v,discovered)
   if stale and v.count in publication_ticks:
    count=counts.get(v.count,0);counts[v.count]=count+1
    if count==0:
     p['body_measured_at']-=.07;p['sent_at']-=.07;p['steering']['measured_at']-=.07
   return p
  root=Path(temp)/name;root.mkdir();result=new.execute(v,x['setup'],original,time.time()+300,Evidence(delay),root,observed,job_class=SavedProducer,pace=False);arrays=[np.array(v.states),np.array(v.controls),np.array(v.requests)];maximum=max(float(abs(a-b).max())for a,b in zip(arrays,saved));adoptions=json.loads((root/'ADOPTIONS.json').read_text());rejected=sum(sum(not a['accepted']for a in row['capture_attempts'])for row in adoptions);assert result['passed']and maximum==0. and result['epochs']==11 and result['maximum_publish_to_control_s']<=.05;assert rejected==(11 if stale else 0);rows.append(dict(case=name,passed=True,software_native=result['new_native'],epochs=11,numeric_maximum_difference=maximum,age_rejected_packets=rejected,max_publish_to_control_s=result['maximum_publish_to_control_s']))
 # The unchanged order must expose a70ms source copy as the observed failure.
 v=Plant();root=Path(temp)/'old_delayed';root.mkdir()
 try:old.execute(v,x['setup'],original,time.time()+300,Evidence(True),root,packet,job_class=SavedProducer,pace=False)
 except AssertionError as e:assert str(e)=='STALE_MEASURED_BODY';old_reproduced=True
 else:raise AssertionError('OLD_DELAY_FAILURE_NOT_REPRODUCED')
# Verify two attempts is an upper bound, and unsafe state/source is not retried.
proposal=proposals[0];buffers=allocate(proposal)
class Fixed:
 count=proposal['packet']['native_tick']
class Source:
 def __init__(self,bad=False):self.bad=bad
 def source(self,v):
  source=copy.deepcopy(proposal['source'])
  if self.bad:source['periodic']['vertices'][0][0][0]+=1.
  return source
negative=[]
for name in ['always_stale','future_time','pose_changed','expanded_source']:
 calls=[0]
 def observed(v,discovered):
  calls[0]+=1;p=copy.deepcopy(proposal['packet']);now=time.monotonic();p.update(sent_at=now,body_measured_at=now);p['steering']['measured_at']=now
  if name=='always_stale':p['body_measured_at']-=.07;p['sent_at']-=.07;p['steering']['measured_at']-=.07
  elif name=='future_time':p['body_measured_at']+=.07;p['sent_at']+=.07;p['steering']['measured_at']+=.07
  elif name=='pose_changed':p['body'][0]+=.002
  return p
 try:capture(buffers,Fixed(),Source(name=='expanded_source'),observed,time.time()+2)
 except AssertionError:assert calls[0]==(2 if name=='always_stale'else 1);negative.append(dict(case=name,rejected=True,packet_reads=calls[0]))
 else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
result=dict(passed=True,rows=rows,old_70ms_delay_failure_reproduced=old_reproduced,negative_cases=negative,models=0,integrations=0,original_50ms_gate_unchanged=True,no_native_steps_in_reacquisition=True,physical_ready=False,no_physical_entrypoint=True,not_a_real_time_guarantee=True);dump(O/'PUBLICATION_QUALIFICATION.json',result);print(json.dumps(result))
