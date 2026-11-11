"""Case definition and constructor binding only; disabled without new authority."""
import contextlib,json,sys,time,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1065_preflight_metadata_continuation_20261111'
@contextlib.contextmanager
def bind_scene(vehicle_module,arena_module,factory_module=None):
 old_w=vehicle_module.W;old_arena=sys.modules.get('arena');old_factory=sys.modules.get('factory');old_initialize=getattr(vehicle_module,'initialize',None);vehicle_module.W=C;sys.modules['arena']=arena_module
 if factory_module is not None:sys.modules['factory']=factory_module;vehicle_module.initialize=factory_module.initialize
 try:yield
 finally:
  vehicle_module.W=old_w
  if factory_module is not None:
   vehicle_module.initialize=old_initialize
   if old_factory is None:sys.modules.pop('factory',None)
   else:sys.modules['factory']=old_factory
  if old_arena is None:sys.modules.pop('arena',None)
  else:sys.modules['arena']=old_arena

def create_vehicle(out,task):
 # The guard is before ANY physical/vehicle/mujoco module import. A future
 # bounded campaign supplies a frozen task table and the fixed09:00 authority.
 # No model construction is possible while the source qualification runs.
 approval=json.loads((O/'APPROVAL.json').read_text());assert approval.get('models_authorized')is True,'PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
 assert time.time()<approval['absolute_deadline_unix']and task['task_id']in approval['allowed_task_ids'],'MISSING_BOUNDED_PHYSICAL_AUTHORITY'
 from kernel import load
 sys.path.insert(0,str(R/'experiments/v858_nav2_verified'))
 import vehicle
 canonical=load('v1061_canonical_scene_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');arena=load('v1061_declared_scene_arena',C/'arena.py')
 factory=load('v1062_gpu_disabled_factory',C/'factory.py')
 with bind_scene(vehicle,arena,factory):instance=canonical.create_vehicle(out,task)
 from cpu_backend import require_cpu_backend
 require_cpu_backend()
 expected=next(x for x in json.loads((C/'SCENE_CASES.json').read_text())if x['id']==task['case_id']);assert instance.count==0 and instance.d.time==0. and list(instance.body()[:2])==expected['start_xy'],'DECLARED_START_NOT_ACTUALLY_BOUND'
 record=dict(course_id='V1061_EW_START_NORTH_010',declared_case=expected,actual_initial_body=list(instance.body()),native=0,integrations_before_binding=0,parent_actor_template_unchanged=True,original_EW_rejection_kept=True);p=Path(out)/'DECLARED_COURSE_BINDING.json';p.write_text(json.dumps(record,indent=2)+'\n');setup=Path(out)/'SETUP.json';x=json.loads(setup.read_text());x['declared_course_id']=record['course_id'];setup.write_text(json.dumps(x,indent=2)+'\n');return instance

def replay(instance,deadline,out):
 from kernel import load
 return load('v1062_exact_replay',R/'experiments/v1020_terminal_two_route_development/physical.py').replay(instance,deadline,out)
