"""Exercise actual production transactions and dispatch method, no ROS/model."""
import ast
import copy
import importlib.abc
import json
import math
import sys
import types
from pathlib import Path
from types import SimpleNamespace as S

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v977_state_consistent_recovery'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('FORBIDDEN_IMPORT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from transaction import RecoveryTransaction,TrackingGuard
from state_reference import REQUIRED
import authority

saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
qualified=json.loads((O/'ZERO_MODEL_QUALIFICATION.json').read_text())
p=saved['rows'][0]['search_packet'];source=saved['rows'][0]['search_source'];plan=qualified['rows'][0]['plan'];now=p['body_measured_at'];goal=plan['original_goal']
checks={}
def expect(name, fn, text):
    try:fn()
    except(AssertionError,PermissionError)as error:checks[name]=text in str(error)
    else:checks[name]=False
def ready():
    tx=RecoveryTransaction(goal,saved['known']);tx.request(p,source,now);tx.canceled(True,5);return tx
tx=RecoveryTransaction(goal,saved['known'])
expect('no_install_before_normal_quiescence',lambda:tx.install(plan,p,source,now),'CANCEL_OR_STOP_NOT_ACKNOWLEDGED')
tx.request(p,source,now)
expect('normal_running_result_cannot_grant_recovery',lambda:tx.canceled(True,2),'NORMAL_ACTION_NOT_QUIESCENT')
tx=ready();effect=tx.install(plan,p,source,now);tx.accepted(True);tx.monitor(p,source,now)
checks['one_controller_and_tighter_goal_checker']=effect['controller_id']=='RecoveryFollowPath'and effect['goal_checker_id']=='recovery_goal_checker'
expect('duplicate_follow_accept_rejected',lambda:tx.accepted(True),'UNEXPECTED_FOLLOW_ACCEPT_CALLBACK')
expect('overlap_recovery_request_rejected',lambda:tx.request(p,source,now),'RECOVERY_ALREADY_ACTIVE')
checks['normal_periodic_plan_cannot_overwrite']=tx.periodic_normal_plan()['action']=='IGNORE_PERIODIC_REFERENCE_OVERWRITE'
bad=copy.deepcopy(p);bad['body'][2]+=.04
expect('online_heading_violation_stops',lambda:tx.monitor_body(bad),'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED')
bad=copy.deepcopy(p);bad['body'][1]+=.1
expect('online_position_violation_stops',lambda:tx.monitor_body(bad),'ONLINE_RECOVERY_POSITION_ENVELOPE_FAILED')
tx=ready();bad=copy.deepcopy(p);bad['steering']['position']=[0.,0.]
expect('steering_drift_requires_new_reference',lambda:tx.install(plan,bad,source,now),'STEERING_DRIFT_REQUIRES_REPLAN')
tx=ready();bad=copy.deepcopy(plan);bad['path'][0][0]+=.01
expect('changed_reference_not_installed',lambda:tx.install(bad,p,source,now),'STATE_REFERENCE_PATH_MISMATCH')
tx=ready();tx.install(plan,p,source,now);tx.accepted(True);tx.path[-1][0]+=.01
expect('committed_path_mutation_stops',lambda:tx.monitor_body(p),'COMMITTED_REFERENCE_MUTATED')
tx=ready();tx.install(plan,p,source,now);tx.accepted(True);tx.follow_completed(4)
bad=copy.deepcopy(p);bad['body'][2]+=.04
expect('tracking_envelope_retained_through_stopping',lambda:tx.monitor_body(bad),'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED')
bad=copy.deepcopy(p);bad['body'][0]=float('nan')
expect('nonfinite_native_pose_rejected',lambda:tx.monitor_body(bad),'NONFINITE_RECOVERY_OBSERVATION')
expect('model_authority_denied',lambda:authority.authorized(), 'NO_PHYSICAL_MODEL_AUTHORITY')

# Extract the unmodified production call-site method, not an equivalent mock.
tree=ast.parse((C/'ros_bridge.py').read_text());method=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='dispatch_command')
class Twist:
    def __init__(self):self.linear=S(x=0.);self.angular=S(z=0.)
context=dict(time=S(monotonic=lambda:now),Twist=Twist,task=dict(goal_xy=goal),json=json,__builtins__=__builtins__)
require_tree=ast.parse((R/'experiments/v862_ready_static/handshake.py').read_text())
require_method=next(x for x in require_tree.body if isinstance(x,ast.FunctionDef)and x.name=='require')
exec(compile(ast.fix_missing_locations(ast.Module(body=[require_method],type_ignores=[])),'original_handshake_require','exec'),context)
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(C/'ros_bridge.py'),'exec'),context)
dispatch=context['dispatch_command'];selected_calls=[]
def admission(packet,src,v,w,known,at):
    return dict(passed=v==0.,v=v,w=w,body_native_tick=packet['native_tick'],source_native_tick=src['source_native_tick'],issued_at=at)
def selection(*args,**kwargs):selected_calls.append(True);raise AssertionError('UNEXPECTED_ALTERNATIVE_MOTION_SELECTION')
modules={'twist_contract':S(require_representable=lambda *a:None),'command_tube':S(admit=admission),'rpccr_recovery':S(select=selection),'snapshot_geometry':S(field=lambda *a:None),'exact_footprint':S(pose_values=lambda *a:None),'cycle_backup':S(stale_proposal_may_defer=lambda *a:False)}
prior={name:sys.modules.get(name)for name in modules}
try:
    sys.modules.update(modules)
    outputs=[];m=Twist();m.linear.x=.05
    fixture=O/'dispatch_negative_fixture';fixture.mkdir(exist_ok=True)
    node=S(latest=dict(phase='RUNNING'),forward=S(request=lambda *a:True),motion=S(decision_snapshot=lambda:(p,source),out=fixture),
           steering_continuity=S(preview=lambda packet,v,w,at:dict(selected=[v,w]),commit=lambda *a:None),
           planner_proxy=S(known=saved['known']),committed_recovery=S(mode='FOLLOW_RECOVERY'),retained_proof=None,
           tube_decisions=[],commands=[],command_sequence=0,send=outputs.append,admission_deferrals=[],guard_failure=None,last_nominal_at=now)
    dispatch(node,m)
    checks['actual_recovery_dispatch_never_selects_other_motion']=not selected_calls and len(outputs)==1 and outputs[0].get('v')==0. and outputs[0].get('w')==0.
    node.committed_recovery=None;outputs.clear();dispatch(node,m)
    checks['dispatch_probe_red_capable_in_normal_mode']=len(selected_calls)==1
finally:
    for name,value in prior.items():
        if value is None:sys.modules.pop(name,None)
        else:sys.modules[name]=value

report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,physical_authority=False,
            actual_dispatch_AST_exercised=True,qualified_reference_threshold=REQUIRED)
(O/'CONTRACT_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
