"""Real dispatch and native ingress, two recorded stopped profiles, zero models."""
import copy,importlib.util,json,sys,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1013_atomic_handoff_software';S=O/'saved'
sys.path.insert(0,str(C))
import reproduce
sys.path.insert(0,str(C))
from command_tube import admit
from steering_continuity import SteeringContinuity
from handoff import release_with_zero
from handshake import require
spec=importlib.util.spec_from_file_location('qualified_atomic_native',C/'native_contract.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def read(p):return json.loads(Path(p).read_text())
def main():
    fault=read(S/'COMMAND_OBSERVATION_FAULT.json');rows=read(S/'RECOVERY_CORRIDORS.json');known=read(S/'physics/SETUP.json')['known'];results=[];negatives=[]
    prior_switch=native.original.switch;switches=[]
    def metadata_switch(vehicle,cls):
        switches.append(cls.__name__);return dict(native_tick=vehicle.count,adapter='V958',last_ctrl=[0.]*4,integral=0.,physical_state_unchanged=True)
    native.original.switch=metadata_switch
    def session(pid,body_tick):
        s=native.Startup('software-handoff');s.phase='RUNNING';s.armed_at=0.;s.last_sequence=100
        v=types.SimpleNamespace(count=body_tick,profile_status=dict(active=False,profile_id=pid,completed_id=pid,released_id=None))
        s.bind_vehicle(v,O);s.holding=True;s.active_profile_id=pid;v.profile_status.update(active=False,profile_id=pid,completed_id=pid,released_id=None)
        return s
    try:
        for row in rows:
            pid=row['profile_id'];packet=copy.deepcopy(row['end_packet']);source=copy.deepcopy(row['end_source']);packet['run_id']='software-handoff'
            now=packet['body_measured_at']+.001;proof=admit(packet,source,0.,0.,known,now);assert proof['passed'],'RECORDED_STOP_CANNOT_FORM_NORMAL_ZERO_TUBE'
            command=dict(kind='command',run_id=packet['run_id'],sequence=101,issued_at=now,v=0.,w=0.,tube=proof)
            release=dict(kind='release_profile',run_id=packet['run_id'],issued_at=now,profile_id=pid,resume_command=command)
            s=session(pid,packet['native_tick']);s.receive(release,now+.005,packet['native_tick']+1,packet['sim_time']+.01)
            assert not s.holding and s.command==command and s.vehicle.profile_status['handoff_sequence']==101
            assert [x['decision']for x in s.receipts]==['PROFILE_RELEASED','ACCEPTED']
            if pid==2:
                node=reproduce.node_with(fault['packet'],fault['source'],proof,label='green_saved_fault')
                node.dispatch_command(types.SimpleNamespace(linear=types.SimpleNamespace(x=0.),angular=types.SimpleNamespace(z=0.)))
                assert node.guard_failure is None and len(node.admission_deferrals)==1 and not node.sent
                assert s.command['v']==s.command['w']==0. and s.command['tube']==proof
                results.append(dict(case='same53.44ms_callback_preserves_only_accepted_stationary_tube',passed=True))
            results.append(dict(case='profile_'+str(pid)+'_atomic_native_release',passed=True,zero_static_lower=proof['static_lower_m'],zero_dynamic_lower=proof['dynamic_lower_m']))
            # Execute the actual supervisor helper, not a handwritten equivalent.
            s1=session(pid,packet['native_tick']);clock=types.SimpleNamespace(value=now);clock.monotonic=lambda:clock.value
            node=types.SimpleNamespace(profile_owner=True,latest=copy.deepcopy(packet),motion=types.SimpleNamespace(decision_snapshot=lambda:(copy.deepcopy(packet),copy.deepcopy(source))),
                planner_proxy=types.SimpleNamespace(known=known),steering_continuity=SteeringContinuity(),command_sequence=100,
                tube_decisions=[],commands=[],retained_proof=None,last_nominal_at=None)
            node.latest['profile_status']=copy.deepcopy(s1.vehicle.profile_status)
            def send(message):
                assert node.profile_owner and node.retained_proof is None
                s1.receive(dict(message,run_id=packet['run_id']),now+.005,packet['native_tick']+1,packet['sim_time']+.01)
                node.latest['profile_status']=copy.deepcopy(s1.vehicle.profile_status);clock.value=now+.005
            node.send=send
            handoff=release_with_zero(node,pid,now+2.,lambda:None,require,clock=clock)
            assert not node.profile_owner and node.retained_proof==node.tube_decisions[-1]['proof']and s1.command['tube']==node.retained_proof
            assert node.command_sequence==101 and node.commands==[[now,0.,0.]]and handoff['stop_ownership_until_ack']
            results.append(dict(case='actual_supervisor_helper_'+str(pid),passed=True))
            if pid==2:
                changes={
                    'missing_zero':lambda p:p.pop('resume_command'),
                    'moving_zero':lambda p:p['resume_command'].update(v=.01),
                    'foreign_run':lambda p:p['resume_command'].update(run_id='foreign'),
                    'future_body':lambda p:p['resume_command']['tube'].update(body_native_tick=packet['native_tick']+100),
                    'old_body':lambda p:p['resume_command']['tube'].update(body_native_tick=packet['native_tick']-100),
                    'old_sequence':lambda p:p['resume_command'].update(sequence=100),
                    'unqualified_tube':lambda p:p['resume_command']['tube'].update(passed=False),
                    'negative_age':lambda p:p['resume_command']['tube'].update(body_age_s=-.001),
                    'age_over50ms':lambda p:p['resume_command']['tube'].update(body_age_s=.051),
                    'wrong_proof_time':lambda p:p['resume_command']['tube'].update(issued_at=now-.1),
                }
                for label,change in changes.items():
                    bad=copy.deepcopy(release);change(bad);s0=session(pid,packet['native_tick']);count=len(switches)
                    try:s0.receive(bad,now+.005,packet['native_tick']+1,packet['sim_time']+.01)
                    except BaseException:
                        assert s0.holding and s0.command is None and len(switches)==count;negatives.append(dict(case=label,rejected_before_owner_release=True))
                    else:raise AssertionError('BAD_HANDOFF_ACCEPTED '+label)
                s0=session(pid,packet['native_tick']);count=len(switches)
                try:s0.receive(release,now+.051,packet['native_tick']+5,packet['sim_time']+.05)
                except AssertionError:assert s0.holding and s0.command is None and len(switches)==count;negatives.append(dict(case='late_delivery',rejected_before_owner_release=True))
                else:raise AssertionError('LATE_HANDOFF_ACCEPTED')
    finally:native.original.switch=prior_switch
    result=dict(passed=True,models=0,integrations=0,scope='Production callback and native release ingress with nonphysical metadata vehicle; original body/geometry/stale guards unchanged',rows=results,negative_cases=negatives,old_fault_reproduced=read(O/'BASELINE_RED.json')['reproduced'])
    (O/'HANDOFF_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,positive_cases=len(results),negative_cases=len(negatives),models=0)))
if __name__=='__main__':main()
