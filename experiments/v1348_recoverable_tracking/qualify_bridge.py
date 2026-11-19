"""Execute the production callback AST, no ROS/model mocks reported as physics."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import time
from segments import direction_allowed
from recovery_guard import check as recovery_reserve

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    tree=ast.parse((C/'ros_component.py').read_text())
    root=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    selected=[n for n in root.body if isinstance(n,ast.FunctionDef) and n.name in ['emit','begin_brake','receive_twist']]
    assert len(selected)==3
    prelude=ast.parse('''
def exercise(v,gear,mode_in='track',dynamic=False,body_in=None):
    sequence=0;latest={};stopped=False;armed=True;rows=[]
    task={'run_id':'qualification','dynamic':dynamic}
    pending_novel=dynamic;reserve_records=[]
    tracker=SimpleNamespace(occupied_ball=lambda _:None)
    known=known_fixture
    segment_counter=1;active_gear=gear;mode=mode_in
    brake_start=0;replan_reason=None;brake_action='plan'
    native_tick=12820;sim_time=128.2;center_body=body_in if body_in is not None else [0.,0.,0.,.05,0.]
    guard_records=[]
    def send(packet): pass
''').body[0]
    prelude.body.extend(selected)
    prelude.body.extend(ast.parse('''
receive_twist(SimpleNamespace(linear=SimpleNamespace(x=v),angular=SimpleNamespace(z=0.)))
return rows,mode,guard_records
''').body)
    import importlib.util
    spec=importlib.util.spec_from_file_location('actual_shared_command_contract',R/'experiments/v1288_baseline_interface/contract.py')
    contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
    known_fixture=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    namespace=dict(known_fixture=known_fixture,recovery_reserve=recovery_reserve,nominal_clearance=lambda *args:999.,time=time,direction_allowed=direction_allowed,command=contract.command,SimpleNamespace=SimpleNamespace)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[prelude],type_ignores=[])),str(C/'ros_component.py'),'exec'),namespace)
    results=[]
    for gear in [1,-1]:
        for requested in [-.05,0.,.05]:
            rows,mode,guards=namespace['exercise'](requested,gear)
            mismatch=requested*gear<0.
            assert len(rows)==1
            assert rows[0]['v']==(0. if mismatch else requested)
            assert (mode=='brake')==mismatch
            if mismatch:assert guards[0]['reason']=='SINGLE_SEGMENT_DIRECTION_MISMATCH'
            results.append(dict(gear=gear,requested=requested,sent=rows[0]['v'],mode=mode))
    # A command arriving during the old action's braking/cancellation cannot
    # enter the new segment: callbacks keep sending zeros until track resumes.
    rows,mode,_=namespace['exercise'](.05,1,'brake')
    assert rows[0]['v']==rows[0]['w']==0. and mode=='brake'
    saved=json.loads((O/'RECOVERY_RESERVE_QUALIFICATION.json').read_text())['first_early_hold']
    rows,mode,guards=namespace['exercise'](.05,1,'track',True,saved['body'])
    assert mode=='brake' and rows[0]['v']==rows[0]['w']==0.
    assert guards[0]['reason']=='KNOWN_STATIC_RECOVERY_RESERVE'
    for f in C.rglob('*.py'):ast.parse(f.read_text(),filename=str(f))
    proof=dict(passed=True,actual_production_callbacks_executed=True,actual_saved_reserve_loss_zero_commanded=True,cases=results,
               in_flight_old_command_during_brake_blocked=True,all_python_parse=True,
               models=0,physical_native=0,ros_process_in_this_test=False)
    (O/'SEGMENT_BRIDGE_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
