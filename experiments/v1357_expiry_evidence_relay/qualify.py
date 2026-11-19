"""Actual expiry and monitor regressions, plus recorded valid-command equivalence."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from stamped_contract import *
from evidence_io import Journal,persist
from worker_monitor import monitor,terminate

C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def load(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def receive_probe(packet,now,started=None):
    """Execute the actual native receive branch, replacing only physical step."""
    tree=ast.parse((C/'native_component.py').read_text())
    root=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    loop=next(n for n in ast.walk(root) if isinstance(n,ast.While) and ast.unparse(n.test)=='not stopped')
    start=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='checked' for t in n.targets))
    # Includes the exact fresh and refused branches plus five actual-step calls.
    end=next(i for i,n in enumerate(loop.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scan' for t in n.targets))
    class OnePacket(ast.NodeTransformer):
        def visit_Continue(self,node):return ast.copy_location(ast.Break(),node)
    # A real receive loop reads a new datagram on continue. This fixture feeds
    # exactly one packet, so terminate that iteration instead of replaying it.
    body=[OnePacket().visit(node) for node in loop.body[start:end]]+ast.parse('break').body
    namespace=dict(time=SimpleNamespace(monotonic=lambda:now),received=packet,task=dict(run_id='probe',algorithm='probe'),
        accepted=-1,v=SimpleNamespace(count=0),received_journal=SimpleNamespace(append=lambda row:None),
        assess_delivery=assess_delivery,validate_delivery=validate_delivery,command=_contract.command,
        active_rejection=None,freshness_rejections=[],freshness_start=started,delivery=None,result={},stopped=False)
    calls=[]
    namespace['step']=lambda v,w,phase:calls.append([v,w,phase])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.While(test=ast.Constant(True),body=body,orelse=[])],type_ignores=[])),str(C/'native_component.py'),'exec'),namespace)
    return calls,namespace


def main():
    O.mkdir(exist_ok=True);checks={}
    old=load('old_gate','experiments/v1356_bounded_motion_relay/stamped_contract.py')
    origin=origin_from_header(1000000000,1010000000,10.)
    packet=dict(kind='command',run_id='probe',sequence=0,issued_at=10.,v=.05,w=.01,origin=origin,
                observation_sequence=1,observation_native_tick=23200,observation_sampled_at=9.99)
    calls,ns=receive_probe(packet,10.01);assert calls==[[.05,.01,'PROBE_ACTUAL_FEEDBACK']]*5
    checks['actual_fresh_receive_branch_preserved']=True
    stale=dict(packet,observation_sampled_at=9.7)
    calls,ns=receive_probe(stale,10.01);assert calls==[[0.,0.,'FRESHNESS_BRAKE_HOLD']]*5
    assert ns['freshness_rejections'][0]['decision']['reason']=='OBSERVATION_EXPIRED'
    checks['actual_stale_receive_branch_only_zero_brakes']=True
    calls,ns=receive_probe(stale,10.01,started=7.)
    assert ns['stopped'] and ns['result']['functional_navigation_stop']=='NO_FRESH_INPUT_FOR_2S'
    checks['actual_persistent_gap_stops_task']=True
    for label,changed in [
        ('source_expired',dict(packet,origin=decode_origin(1000000000,1300000000,10.))),
        ('envelope_expired',dict(packet,issued_at=9.5))]:
        calls,ns=receive_probe(changed,10.01);assert all(v==w==0. for v,w,_ in calls)
        checks[label+'_zero_braked']=True
    for label,changed in [
        ('foreign',dict(packet,run_id='foreign')),('replayed',dict(packet,sequence=-1)),
        ('future_observation',dict(packet,observation_sampled_at=11.)),('nonfinite',dict(packet,v=float('nan'))),
        ('speed',dict(packet,v=.2)),('curvature',dict(packet,w=.1)),
        ('local_nonzero',dict(packet,origin=local_zero(10.))),
        ('origin_tamper',dict(packet,origin=dict(origin,generated_monotonic=10.)))]:
        try:receive_probe(changed,10.01)
        except (AssertionError,ValueError):checks[label+'_hard_refused']=True
        else:raise AssertionError('NEGATIVE_NOT_REJECTED '+label)
    examined=0
    for role in ['main','repeat']:
        out=R/('runs/v858_nav2_verified/v1354/rpp_fast_stamped_static_'+role)
        commands={row['sequence']:row for row in json.loads((out/'ROS_COMMANDS.json').read_text())}
        journal=json.loads((out/'APPLIED_JOURNAL.json').read_text());seen=set()
        for event in journal:
            if event.get('delivery') is None or event['command_sequence'] in seen:continue
            seq=event['command_sequence'];seen.add(seq);command=commands[seq];now=event['delivery']['validated_monotonic']
            assert validate_delivery(command,now)==old.validate_delivery(command,now)==event['delivery']
            assert assess_delivery(command,now,run_id=command['run_id'],previous_sequence=seq-1)['accepted'];examined+=1
    checks['all_saved_static_deliveries_equivalent']=examined>3000
    ros=load('ros_env','experiments/v856_nav2_foundation/ros_environment.py')
    folder=O/'cooperative_peer_close';folder.mkdir(exist_ok=False)
    with (folder/'peer.console').open('x') as log:
        peer=subprocess.Popen(ros.command(['/usr/bin/python3.12','-B',str(C/'peer_fixture.py'),str(folder),'cooperative',str(time.monotonic()+15)]),cwd=R,env=ros.environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            end=time.monotonic()+5
            while not (folder/'READY.json').exists() and time.monotonic()<end:
                assert peer.poll() is None;time.sleep(.01)
            assert (folder/'READY.json').exists()
            native=subprocess.Popen([sys.executable,'-B','-c','pass'],start_new_session=True)
            close=monitor([peer,native],folder,remaining=lambda:20.,task_seconds=15)
        finally:terminate(peer)
    assert json.loads((folder/'ROS_RESULT.json').read_text())['closed'] and (folder/'ROS_COMMANDS.json').exists()
    assert close['cooperative_ros_close_requested'] and peer.returncode==0
    checks['actual_wrapper_cooperative_close_preserves_evidence']=True
    folder=O/'persist_fixture';folder.mkdir(exist_ok=False)
    journal=Journal(folder/'commands.jsonl');journal.append(dict(v=.1,w=0.));journal.close()
    result=persist(folder,[('ROS_COMMANDS.json',[dict(v=.1,w=0.)])],dict(passed=True),closed=True)
    assert result['closed'] and not result['evidence_write_errors']
    (folder/'bad_target').mkdir()
    result=persist(folder,[('bad_target',[])],dict(passed=True),closed=True)
    assert not result['passed'] and result['evidence_write_errors']
    checks['write_failure_explicitly_not_passed']=True
    proof=dict(passed=all(checks.values()),checks=checks,actual_saved_deliveries_examined=examined,
        cooperative_monitor=close,production_receive_AST_executed=True,models=0,physical_native=0)
    (O/'EXPIRY_AND_CLOSE_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(passed=proof['passed'],checks=len(checks),saved_deliveries=examined,models=0)))


if __name__=='__main__':
    from stamped_contract import _contract
    main()
