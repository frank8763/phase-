"""Replay the real production dispatch callback on the saved 53.44ms fault."""
import ast,copy,importlib.abc,json,sys,types
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1013_atomic_handoff_software';S=O/'saved'
sys.path[:0]=[str(R/'experiments'/p)for p in ['v1009_explicit_checker_navigation','v1004_planned_input_navigation','v947_rpccr_forward_commitment','v891_dynamic_consistency_software','v884_feasible_rpp']]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('SOFTWARE_ONLY '+name)
sys.meta_path.insert(0,NoModel())
from handshake import require
from navigation_policy import ForwardNavigation
def read(p):return json.loads(Path(p).read_text())
def dispatch_method():
    source=R/'experiments/v1004_planned_input_navigation/ros_bridge.py';tree=ast.parse(source.read_text());function=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='dispatch_command')
    scope=dict(require=require,json=json,time=types.SimpleNamespace(monotonic=lambda:read(S/'COMMAND_OBSERVATION_FAULT.json')['checked_at']),Twist=lambda:types.SimpleNamespace(linear=types.SimpleNamespace(x=0.),angular=types.SimpleNamespace(z=0.)),task=dict(goal_xy=[4.,-2.]))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(source),'exec'),scope)
    return scope['dispatch_command']
def node_with(packet,source,proof=None,label='red'):
    out=O/label;out.mkdir(exist_ok=True);sent=[]
    node=types.SimpleNamespace(latest=copy.deepcopy(packet),profile_owner=False,forward=ForwardNavigation([4.,-2.]),
        motion=types.SimpleNamespace(out=out,decision_snapshot=lambda:(copy.deepcopy(packet),copy.deepcopy(source))),
        retained_proof=proof,guard_failure=None,admission_deferrals=[],send=lambda p:sent.append(p))
    node.dispatch_command=types.MethodType(dispatch_method(),node);node.sent=sent
    return node
def main():
    fault=read(S/'COMMAND_OBSERVATION_FAULT.json');node=node_with(fault['packet'],fault['source'])
    m=types.SimpleNamespace(linear=types.SimpleNamespace(x=0.),angular=types.SimpleNamespace(z=0.))
    node.dispatch_command(m)
    assert node.guard_failure=="ProtocolError('STALE_COMMAND_BODY')"and node.sent[0]['kind']=='stop'
    result=dict(reproduced=True,models=0,integrations=0,production_dispatch_callback=True,age_s=fault['checked_at']-fault['packet']['body_measured_at'],fault=node.guard_failure,cleared_permission_causes_stop=True)
    (O/'BASELINE_RED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
