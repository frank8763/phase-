"""Zero-model path/audit regressions plus exact dependency/table contracts."""
import ast,copy,importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v968_rpp_closed_loop_night'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from closed_handoff import curve_path,continuation_path
from component_audit import independent_continuation,tracking
from steering_continuity import SteeringContinuity
from authority import root_authorized
saved=R/'runs/v858_nav2_verified/v962/handoff_left'
with np.load(saved/'HANDOFF_ARRAYS.npz')as f:body=f['body'];ref=f['expected'];enc=f['steering']
packet=dict(native_tick=420,body=body[419].tolist(),body_measured_at=1.,steering=dict(native_tick=420,measured_at=1.,position=enc[419,:2].tolist(),velocity=enc[419,2:].tolist()))
path=continuation_path(packet);independent=independent_continuation(packet);curve=curve_path([-4.,-2.,0.])
checks=dict(full1200_forward_path=len(path)==1201,independent_causal_curve_exact=np.max(abs(path-independent))<=1e-9,
    first_curve_201_samples=len(curve)==201,path_origin_measured=np.array_equal(path[0],packet['body'][:3]),
    old_actual_openloop_failure_remains_red=not tracking(ref,body[420:])['passed'],
    no_reverse_reference=all((np.array(b[:2])-a[:2])@np.array([np.cos(a[2]),np.sin(a[2])])>0 for a,b in zip(path,path[1:])),
    exact_reference_is_green=tracking(path,np.asarray(path))['passed'])
bad=np.asarray(path).copy();bad[:,:2]+=.05*np.c_[-np.sin(bad[:,2]),np.cos(bad[:,2])]
checks['lateral_path_fault_rejected']=not tracking(path,bad)['passed']
bad=np.asarray(path).copy();bad[:,2]+=.04
checks['heading_fault_rejected']=not tracking(path,bad)['passed']
checks['unchanged_command_admission_and_adapter']=all((C/name).read_bytes()==(R/'experiments/v963_continuous_dynamic'/name).read_bytes()for name in ['command_tube.py','certified_contract.py','native_contract.py','cycle_backup.py','polygon_geometry.py','periodic_support.py','steering_continuity.py','physical.py'])
tasks=json.loads((C/'TASKS.json').read_text());previous=json.loads((R/'experiments/v963_continuous_dynamic/NIGHT_TASKS.json').read_text());fixed=[x for x in tasks if x['stage']=='confirmation'];old=[x for x in previous if x['stage']=='confirmation']
checks.update(unique34tasks=len(tasks)==34==len({x['run_id']for x in tasks}),original_locked24_science_preserved=all(all(a[k]==b[k]for k in ['seed','phase','case_id','goal_xy','goal_yaw','slot','initial_axis_direction','route'])for a,b in zip(fixed,old)),
    balanced_routes=all(sum(x['route']==r for x in fixed)==8 for r in ['we','ns','ew']),balanced_directions=all(sum(x['initial_axis_direction']==d for x in fixed)==12 for d in [-1,1]),
    fixed_repeat_slots=[x['slot']for x in tasks if x['stage']=='confirmation_repeat']==[1,9,17])
try:root_authorized()
except(FileNotFoundError,AssertionError):checks['no_model_authority_before_freeze']=True
else:checks['no_model_authority_before_freeze']=False
import native_worker
sys.path.insert(0,str(C));import supervise,watchdog,transaction,recovery,corridor_search,polygon_geometry
checks['actual_native_dependency']=native_worker.engine.C==C
checks['actual_supervisor_dependency']=all(Path(m.__file__).parent==C for m in [supervise,watchdog,transaction,recovery,corridor_search,polygon_geometry])
for folder in [C,R/'experiments/v969_rpp_night_closure']:
    for p in folder.glob('*.py'):ast.parse(p.read_text(),str(p))
checks['all_source_AST']=True
checks['full_real_RPP_software']=json.loads((O/'FULL_COMPONENT_SOFTWARE_QUALIFICATION.json').read_text())['passed']
checks['real_pre_goal_startup']=json.loads((O/'FULL_STARTUP_QUALIFICATION.json').read_text())['passed']
result=dict(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},models=0,integrations=0,
    scope='Saved failure red-capable spatial/heading audits, independent causal reference generation, unchanged runtime/physics and task tables; actual RPP software fixture separate, not physical qualification.')
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
