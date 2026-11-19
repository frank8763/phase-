"""Actual production callback red: admissible22cm route, unconditional25cm stop."""
import ast
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1359_reverse_restart_bridge'))
from observed_route import nominal_clearance


def main():
    O.mkdir(exist_ok=True)
    raw=R/'runs/v858_nav2_verified/v1359/sweep_terminal_dynamic_main'
    plan=next(v for v in json.loads((raw/'CAUSAL_ROUTE_RECORDS.json').read_text()) if v['index']==10)
    current=nominal_clearance(plan['body'],plan['ball'][:2],plan['ball'][2])
    assert .22<current<.25 and plan['live_result_validation']['minimum_clearance_m']>=.22
    tree=ast.parse((R/'experiments/v1359_reverse_restart_bridge/ros_component.py').read_text())
    root=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    callback=next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='receive_body_twist')
    branch=next(n for n in callback.body if isinstance(n,ast.If) and ast.unparse(n.test)=="task['dynamic']")
    # Only the actual two-statement dynamic future-reserve boundary is needed:
    # known field/control-safety/gear paths are not involved in this refusal.
    statements=branch.body[:2];brakes=[]
    ns=dict(tracker=SimpleNamespace(occupied_ball=lambda t:(plan['ball'][:2],plan['ball'][2])),
        sim_time=0.,center_body=plan['body'],nominal_clearance=nominal_clearance,begin_brake=brakes.append)
    exec(compile(ast.fix_missing_locations(ast.Module(body=statements,type_ignores=[])),str(R/'experiments/v1359_reverse_restart_bridge/ros_component.py'),'exec'),ns)
    assert brakes==['CAUSAL_FUTURE_BALL_RESERVE']
    value=dict(reproduced=True,saved_request=10,native_tick=plan['native_tick'],body=plan['body'],ball=plan['ball'],
        current_dynamic_clearance_m=current,original_route_minimum_m=plan['live_result_validation']['minimum_clearance_m'],
        planning_required_m=.22,unconditional_brake_m=.25,stationary_body=plan['body'][3:],
        actual_callback_AST_triggered_brake=True,models=0,physical_native=0)
    (O/'ORIGINAL_REPRODUCTION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
