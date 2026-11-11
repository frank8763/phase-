"""Independent current fixed-clock and preserved classic-WE software audits."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from handoff import prepare
pin_threads();old=load('v1061_original_classic_producer',R/'experiments/v1058_fresh_repeat_entry/handoff.py');sys.path.insert(0,str(C));rows=[]
for folder in ['ns_synthetic_contract_fixed_clock','ns_synthetic_contract_fixed_clock_transient']:
 payload=json.loads((O/folder/'INPUT.json').read_text());p=json.loads((O/folder/'RESULT.json').read_text());assert p['passed']and p['actual_job_wall_s']<8.
 n=p['pre_adoption_hold_native'];wait=p['fixed_launch_wait'];actions=[dict(kind='wait',gear=0,target=0.,ticks=n)]+p['prefix']+[dict(kind='wait',gear=0,target=0.,ticks=wait)]+p['suffix'];ss,uu,rr,mm=predict(payload['setup'],payload['packet'],actions,tail=False)
 actual_s=np.vstack([p['prefix_states'],np.asarray(p['wait_states'])[1:],np.asarray(p['cross_states'])[1:]]);actual_u=np.vstack([p['prefix_controls'],p['wait_controls'],p['cross_controls']]);actual_r=np.vstack([p['prefix_requests'],np.zeros((wait,3)),p['cross_requests']]);error=dict(states=float(abs(ss[n:]-actual_s).max()),controls=float(abs(uu[n:]-actual_u).max()),requests=float(abs(rr[n:]-actual_r).max()));assert max(error.values())==0.
 low=Geometry(payload['setup']['known'],payload['source']['periodic'],payload['packet']['sim_time']+.01*n).complete(ss[n:]);packet=dict(controller_memory=dict(last_ctrl=mm[n,:4].tolist(),integral=float(mm[n,4])));cc,upper=checks(ss[n:],uu[n:],rr[n:],packet,payload['setup'],np.array(payload['goal']),low,REQUIRED);assert all(cc.values())and abs(low-p['launch_bounds'][0])<=1e-12 and p['expected_publication_native']==payload['packet']['native_tick']+n and p['expected_publication_sim_time']==payload['packet']['sim_time']+.01*n
 rows.append(dict(case=folder,passed=True,maximum_differences=error,checks=cc,minimum_raw_m=low,goal_upper_m=upper,producer_wall_s=p['actual_job_wall_s'],synthetic_source_only=True,not_actual_NS_dynamic_qualification=True))
x=json.loads((O/'dependencies/WE_MEASURED_INPUT.json').read_text());actions=json.loads((C/'RECOVERY_WARM_SEED.json').read_text())['actions'];arguments=dict(setup=x['setup'],packet=x['packet'],source=x['source'],goal=x['goal'],actions=actions,elapsed=0);previous=old.prepare(**arguments);updated=prepare(**arguments);keys=['prefix_states','prefix_controls','prefix_requests','wait_states','wait_controls','cross_states','cross_controls','cross_requests','launch_bounds'];maximum={k:float(np.max(abs(np.array(updated[k])-previous[k])))for k in keys};assert max(maximum.values())==0.;rows.append(dict(case='WE_CLASSIC_PRODUCER_UNCHANGED',passed=True,maximum_differences=maximum))
publication=json.loads((O/'FIXED_CLOCK_PUBLICATION_AUDIT.json').read_text());assert publication['passed'];rows.append(dict(case='CURRENT_FIXED_CLOCK_PUBLICATION_AND_NEGATIVES',passed=True,audit='FIXED_CLOCK_PUBLICATION_AUDIT.json'))
result=dict(passed=True,rows=rows,models=0,mujoco_integrations=0,software_only=True,original_canonical_NS_dynamic_qualified=False);dump(O/'INDEPENDENT_SOFTWARE_AUDIT.json',result);print(json.dumps(result))
