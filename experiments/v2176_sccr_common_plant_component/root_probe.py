"""New production namespace/root refusal, no real component authorization."""
from pathlib import Path
import os,sys,json
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from context import R,SOURCE as S,O,read
assert C.name=='v2176_sccr_common_plant_component'and S==R/'runs'/C.name and O==S/'components/SCCR'
assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)and os.environ['CUDA_VISIBLE_DEVICES']==''and not(O/'PILOT_ADMISSION.json').exists()
import policy,union_sampler
task=read(O/'PILOT_TASK.json');assert task['output']==str(O/'actual')
class NoVehicle:
 def __getattribute__(self,n):raise AssertionError('VEHICLE_ACCESS_BEFORE_ADMISSION')
cases=[]
for label,fn in [('107_actor',lambda:policy.FrozenActor(107)),('186_actor',lambda:policy.FrozenActor(186)),('sampler',lambda:union_sampler.Sampler(NoVehicle(),None,None,None,None,None,task,{},None))]:
 try:fn()
 except FileNotFoundError as e:assert Path(e.filename)==O/'PILOT_ADMISSION.json';cases.append(label)
 else:raise AssertionError('NEW_ROOT_ADMISSION_NOT_REFUSED')
assert 'torch'not in sys.modules and 'mujoco'not in sys.modules
print(json.dumps(dict(passed=True,scope='NEW_ISOLATED_SOURCE_ROOT_BINDING_ONLY',cases=cases,new_source=str(S),new_component=str(O),Torch_imports=0,MuJoCo_imports=0,models=0,NN_inference=0,physics=0)))
