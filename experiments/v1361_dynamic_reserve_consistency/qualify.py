"""Actual saved production callback red/green and real installed RPP commands."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from dynamic_reserve import check
from dynamic_audit import reconstruct

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def callback(path):
    root=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    return next(n for n in root.body if isinstance(n,ast.FunctionDef) and n.name=='receive_body_twist')


def main():
    x=json.loads((C/'INPUT_00.json').read_text());body=x['original_body'];ball=x['causal_ball'];checks={}
    old=callback(R/'experiments/v1359_reverse_restart_bridge/ros_component.py');new=callback(C/'ros_component.py')
    strip=lambda node:[ast.dump(n,include_attributes=False) for n in node.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=="task['dynamic']")]
    assert strip(old)==strip(new);checks['entire_static_callback_AST_unchanged']=True
    rows=json.loads((O/'software/saved_request10_reverse_escape/RAW_COMMANDS.json').read_text())
    moving=[r for r in rows if abs(r['v'])>=.005];assert len(moving)>=20
    for row in moving:
        allowed,p=check(body,ball,row['v'],row['w']);ind,current,values=reconstruct(body,ball,row['v'],row['w'])
        assert allowed and ind and p['command_geometry_minimum_m']>=.22 and values[-1]>current
    checks['actual_installed_RPP_saved_escape_commands_pass']=True
    ns=dict(tracker=SimpleNamespace(occupied_ball=lambda _: (np.array(ball[:2]),ball[2])),sim_time=x['original_sim_time'],
            center_body=body,native_tick=x['native_tick'],value=SimpleNamespace(linear=SimpleNamespace(x=moving[0]['v']),angular=SimpleNamespace(z=moving[0]['w'])),
            dynamic_reserve=check,dynamic_reserve_records=[],sequence=0,mode='track',guard_records=[])
    brakes=[]
    def brake(reason):
        brakes.append(reason);ns['mode']='brake';ns['guard_records'].append({})
    ns['begin_brake']=brake
    branch=next(n for n in new.body if isinstance(n,ast.If) and ast.unparse(n.test)=="task['dynamic']")
    exec(compile(ast.fix_missing_locations(ast.Module(body=branch.body[:2],type_ignores=[])),str(C/'ros_component.py'),'exec'),ns)
    assert not brakes and ns['dynamic_reserve_records'][0]['allowed'];checks['actual_production_callback_saved_red_now_green']=True
    toward=check(body,ball,.08,0.);assert not toward[0];checks['toward_occupancy_refused']=True
    # A deliberately constructed below-floor pose is a boundary fixture, not an actual trial.
    low=body[:];low[0]+=.05
    assert not check(low,ball,-.08,0.)[0];checks['below22cm_nonzero_refused']=True
    assert check(body,ball,0.,0.)[0] and check(low,ball,0.,0.)[0];checks['exact_zero_braking_always_allowed']=True
    assert not check(body,ball,1e-5,0.)[0];checks['small_nonzero_toward_command_not_zero_bypass']=True
    count=0;maximum=0.
    for v in np.linspace(-.1,.1,9):
        for curvature in np.linspace(-1/1.32,1/1.32,9):
            w=float(v*curvature);passed,p=check(body,ball,float(v),w);expected,current,values=reconstruct(body,ball,float(v),w)
            assert passed==expected;maximum=max(maximum,abs(current-p['current_dynamic_clearance_m']));count+=1
    checks['independent_scalar_geometry_and_direction_boundaries']=maximum<=1e-8
    for b,field in [(body[:4],ball),(body,[*ball[:2],-1.]),([float('nan'),*body[1:]],ball)]:
        try:check(b,field,-.08,0.)
        except AssertionError:pass
        else:raise AssertionError('MALFORMED_GUARD_INPUT_ACCEPTED')
    checks['malformed_nonfinite_and_negative_radius_refused']=True
    result=dict(passed=all(checks.values()),checks=checks,actual_saved_request=10,actual_RPP_moving_commands=len(moving),
                boundary_cases=count,first_actual_command=[moving[0]['v'],moving[0]['w']],first_preview=check(body,ball,moving[0]['v'],moving[0]['w'])[1],
                independent_scalar_maximum_error_m=maximum,models=0,physical_native=0,static_trials_reused_not_new=True)
    (O/'CHANGED_BOUNDARY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
