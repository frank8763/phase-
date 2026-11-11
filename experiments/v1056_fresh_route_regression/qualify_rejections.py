"""Production gate rejection cases; analytical arrays only."""
import copy,sys,time,json,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from atomic import allocate,publish
from fresh import finite_plan
proposal=json.loads((R/'runs/v1054_atomic_publish/software_full_executor/refresh/epoch00/RESULT.json').read_text());buffers=allocate(proposal);negative=[]
for name,mutate in [('stale_body',lambda p,s:p.update(sent_at=p['sent_at']+.051)),('encoder_tick',lambda p,s:p['steering'].update(native_tick=p['native_tick']+1)),('pose_drift',lambda p,s:p['body'].__setitem__(0,p['body'][0]+.002)),('memory',lambda p,s:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.01)),('future_source',lambda p,s:s.update(source_native_tick=p['native_tick']+1)),('stale_sensor',lambda p,s:s.update(source_age_s=.052)),('expanded_domain',lambda p,s:s['periodic']['vertices'][0][0].__setitem__(0,s['periodic']['vertices'][0][0][0]+1.))]:
 p=copy.deepcopy(proposal['packet']);source=copy.deepcopy(proposal['source']);now=time.monotonic();p.update(sent_at=now,body_measured_at=now);p['steering']['measured_at']=now;mutate(p,source)
 try:publish(buffers,p,source,p['sent_at'])
 except AssertionError:negative.append(name)
 else:raise AssertionError('UNREJECTED '+name)
try:buffers.prefix_states[0,0]+=1.
except ValueError:negative.append('readonly_buffers')
else:raise AssertionError('MUTABLE_BUFFERS')
meta=json.loads((O/'WEST_EAST_T0_METADATA.json').read_text());bad=copy.deepcopy(meta['packet']);bad['body'][:2]=meta['setup']['known']['known_rectangles'][0][:2];plan=finite_plan(meta['setup'],bad,None,np.zeros((200,3)),'INVALID_GEOMETRY');assert not plan['passed'];negative.append('unsafe_static_pose')
dump(O/'REJECTION_QUALIFICATION.json',dict(passed=True,negative_cases=negative,models=0,integrations=0));print(json.dumps(negative))
