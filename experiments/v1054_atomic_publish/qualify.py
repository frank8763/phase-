"""Same actual failed publication, equivalence, clock gate and timing samples."""
import copy,importlib.abc,sys,time,json,math
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1054_atomic_publish';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import pin_threads,load,predict,checks,Geometry,REQUIRED,sha,dump
from atomic import allocate,publish
old=load('v1054_previous_publication',R/'experiments/v1053_parked_refresh_handoff/handoff.py')
def main():
 cpu=pin_threads();proposal=json.loads((O/'inputs/RESULT.json').read_text());actual=json.loads((O/'inputs/ADOPTED_PLAN.json').read_text());setup=json.loads((O/'inputs/SETUP.json').read_text());assert proposal['passed'];buffers=allocate(proposal);source_sha=sha(O/'inputs/RESULT.json');rows=[];timings=[]
 for delay in [0,50,500,1100]:
  packet=copy.deepcopy(actual['published_packet']);source=copy.deepcopy(proposal['source']if delay<800 else actual['publication_source']);packet['native_tick']=proposal['packet']['native_tick']+delay;packet['sim_time']=proposal['packet']['sim_time']+delay*.01;packet['sent_at']=time.monotonic();packet['body_measured_at']=packet['sent_at'];packet['steering'].update(native_tick=packet['native_tick'],measured_at=packet['sent_at']);source.update(source_native_tick=packet['native_tick'],source_age_s=0.,decision_at=packet['sent_at']);start=time.monotonic();view=publish(buffers,packet,source,start);request=view.request(0);elapsed=time.monotonic()-packet['body_measured_at'];assert elapsed<=.05,'ATOMIC_PUBLICATION_EXPIRED';record=view.record();legacy=old.publish(proposal,packet,source,packet['sent_at']);assert view.wait==legacy['phase_wait_ticks'];assert np.array_equal(record['state_path'],legacy['state_path']);assert np.array_equal(record['predicted_actuator_controls'],legacy['predicted_actuator_controls']);assert np.array_equal(record['planned_body_requests'],legacy['planned_body_requests']);assert record['actions']==legacy['actions'];assert all(np.array_equal(view.request(i),np.array(record['planned_body_requests'][i]))for i in range(view.native_steps));assert all(np.array_equal(view.state(i),np.array(record['state_path'][i]))for i in range(view.native_steps+1));ss,uu,rr,mm=predict(setup,proposal['packet'],record['actions'],tail=False);assert abs(ss-np.array(record['state_path'])).max()<=1e-8;geometry=Geometry(setup['known'],proposal['source']['periodic'],packet['sim_time']);low=geometry.complete(ss);cc,upper=checks(ss,uu,rr,proposal['packet'],setup,np.array(proposal['goal']),low,REQUIRED);assert all(cc.values());rows.append(dict(delay_native=delay,selected_wait=view.wait,first_control_wall_s=elapsed,minimum_raw_m=low,goal_upper_m=upper,native_states=len(ss),exact_same_controls_and_states_as_old=True))
 # Benchmark the production critical path on one CPU. Allocate and prepare
 # the latest coherent packet BEFORE starting each measured publication.
 for i in range(500):
  packet=copy.deepcopy(actual['published_packet']);source=copy.deepcopy(actual['publication_source']);now=time.monotonic();packet.update(sent_at=now,body_measured_at=now);packet['steering']['measured_at']=now;view=publish(buffers,packet,source,now);command=view.request(0);timings.append(time.monotonic()-now)
 assert max(timings)<=.05
 negatives=[]
 for name,mutate in [('stale',lambda p,s:p.update(sent_at=p['sent_at']+.051)),('encoder_tick',lambda p,s:p['steering'].update(native_tick=p['native_tick']+1)),('pose_drift',lambda p,s:p['body'].__setitem__(0,p['body'][0]+.002)),('memory',lambda p,s:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.01)),('future_source',lambda p,s:s.update(source_native_tick=p['native_tick']+1)),('stale_sensor',lambda p,s:s.update(source_age_s=.052)),('expanded_source',lambda p,s:s['periodic']['vertices'][0][0].__setitem__(0,s['periodic']['vertices'][0][0][0]+1.))]:
  packet=copy.deepcopy(actual['published_packet']);source=copy.deepcopy(actual['publication_source']);mutate(packet,source)
  try:publish(buffers,packet,source,packet['sent_at'])
  except AssertionError:negatives.append(name)
  else:raise AssertionError('UNREJECTED '+name)
 try:buffers.prefix_states[0,0]+=1.
 except ValueError:negatives.append('readonly_nominal_array')
 else:raise AssertionError('MUTABLE_NOMINAL')
 assert sha(O/'inputs/RESULT.json')==source_sha;result=dict(passed=True,rows=rows,timing=dict(samples=len(timings),maximum_s=max(timings),p99_s=float(np.quantile(timings,.99)),median_s=float(np.median(timings)),unchanged_deadline_s=.05,single_cpu=cpu),negative_cases=negatives,source_proposal_sha256=sha(O/'inputs/RESULT.json'),models=0,integrations=0,actual_dynamic_accepted=False,physical_ready=False);dump(O/'QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
