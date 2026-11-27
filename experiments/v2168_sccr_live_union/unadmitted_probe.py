"""Real isolated namespace: all production constructors refuse before models."""
from pathlib import Path
import sys,os,json
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from context import R,O,SOURCE,read
assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)and os.environ['CUDA_VISIBLE_DEVICES']==''
assert not(O/'PILOT_ADMISSION.json').exists()and not(SOURCE/'SOURCE_ONCE.json').exists()
import policy,union_sampler,private_snapshot
task=read(O/'PILOT_TASK.json');cases=[]
class NoLiveObject:
 def __getattribute__(self,name):raise AssertionError('LIVE_OBJECT_TOUCHED_BEFORE_ADMISSION')
def check(name,fn):
 try:fn()
 except FileNotFoundError as e:assert Path(e.filename)==O/'PILOT_ADMISSION.json';cases.append(name)
 else:raise AssertionError('UNADMITTED_CONSTRUCTOR_ACCEPTED:'+name)
check('original_107_actor_before_Torch',lambda:policy.FrozenActor(107))
check('original_186_actor_before_Torch',lambda:policy.FrozenActor(186))
check('full_sampler_before_vehicle_or_renderer',lambda:union_sampler.Sampler(NoLiveObject(),None,None,None,None,None,task,{}))
check('private_geometry_before_model_read',lambda:private_snapshot.live(None,NoLiveObject(),None,None,None,task,None,None))
assert 'torch'not in sys.modules and 'mujoco'not in sys.modules
v=dict(passed=True,scope='ACTUAL_PHASE_ISOLATED_NAMESPACE_UNADMITTED_PRODUCTION_ENTRY',cases=cases,Torch_imports=0,MuJoCo_imports=0,models=0,renderer_constructors=0,weight_loads=0,forward_calls=0,physics=0,source_once_claimed=False)
target=Path(sys.argv[1]);assert target.parent.name=='software_cli'and target.name=='NAMESPACE_PROBE.json';target.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
