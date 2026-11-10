"""Production supervisor with real saved causal packets and non-ROS action peers.

The actual watchdog, constructor, transaction, binding call site and resume path
run together. Futures emulate only action-server responses; no physical model.
"""
import copy
import importlib.abc
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace as S

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v977_state_consistent_recovery'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import supervise
from transaction import RecoveryTransaction
from watchdog import ReferenceWatchdog

saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
plans=json.loads((O/'ZERO_MODEL_QUALIFICATION.json').read_text())['rows']
checks={};rows=[]

class Future:
    def __init__(self,value,finished=True):self.value=value;self.finished=finished
    def done(self):return self.finished
    def result(self):return self.value


def run_case(index):
    record=saved['rows'][index]
    initial=record['search_packet'];source=record['search_source'];goal=record['original_goal']
    plan=plans[index]['plan'];events=[];observed=[];phase={'at_endpoint':False,'normal_calls':0}
    normal_future=Future(S(status=2,result=S(error_code=0)),False)
    class Handle:
        accepted=True
        def get_result_async(self):return normal_future
        def cancel_goal_async(self):
            events.append('NORMAL_CANCEL_ACK');normal_future.value=S(status=5,result=S(error_code=0));normal_future.finished=True
            return Future(S(goals_canceling=[True]))
    def send_goal(goal_message):
        phase['normal_calls']+=1
        events.append('NORMAL_GOAL_'+str(phase['normal_calls']))
        if phase['normal_calls']>=2:
            normal_future.value=S(status=4,result=S(error_code=0));normal_future.finished=True
        return Future(Handle())
    def snapshot():
        packet=copy.deepcopy(initial);src=copy.deepcopy(source);now=time.monotonic()
        packet['body_measured_at']=packet['sent_at']=now
        packet['steering']['measured_at']=now
        if phase['at_endpoint']:
            packet['body'][:3]=plan['path'][-1]
            # Preserve original compatible stopped encoders; no synthetic
            # actuator response is asserted by this action-protocol test.
        src['decision_at']=now;src['source_age_s']=0.
        return packet,src
    folder=O/f'supervision_case{index}';folder.mkdir(exist_ok=False)
    node=S(forward=S(resume=lambda x:events.append('FORWARD_RESUME'),reference=lambda x:events.append('REFERENCE_INSTALLED'),replan_requested=False),
           get_clock=lambda:S(now=lambda:S(to_msg=lambda:None)),action=S(send_goal_async=send_goal),
           motion=S(out=folder,decision_snapshot=snapshot),planner_proxy=S(known=saved['known'],rows=[]),tube_decisions=[],guard_failure=None,
           committed_recovery=None)
    class FastWatchdog(ReferenceWatchdog):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            assert isinstance(self.transaction,RecoveryTransaction),'WRONG_TRANSACTION_BINDING'
            if phase['normal_calls']==1:
                now=time.monotonic()
                for at in [now-2.,now-1.8,now-1.6]:self.detector.route(at,False)
                self.detector.poses=[(now-1.51,*initial['body'][:2])]
        def poll(self,*args):
            event=super().poll(*args)
            if event:observed.append(event)
            return event
    class Binding:
        def __init__(self,n):self.client=S(server_is_ready=lambda:True)
        def send(self,effect):
            assert normal_future.done() and normal_future.result().status==5,'RECOVERY_ACTION_OVERLAP'
            assert effect['controller_id']=='RecoveryFollowPath'and effect['goal_checker_id']=='recovery_goal_checker'
            assert node.committed_recovery is not None,'MISSING_COMMAND_OWNERSHIP'
            events.append('ONE_RECOVERY_FOLLOW_SENT');phase['at_endpoint']=True
            return Future(S(accepted=True,get_result_async=lambda:Future(S(status=4,result=S(error_code=0)))))
    prior_watchdog,prior_binding=supervise.ReferenceWatchdog,supervise.FollowPathBinding
    supervise.ReferenceWatchdog=FastWatchdog;supervise.FollowPathBinding=Binding
    message=S(pose=S(header=S(stamp=None),pose=S(position=S(x=goal[0],y=goal[1]))))
    def require(condition,reason):assert condition,reason
    def wait(node,predicate,until,message):assert predicate(),message
    try:
        result,reported=supervise.supervise(node,message,time.monotonic()+20,time.time()+100,
                                          lambda *a,**k:time.sleep(.001),wait,require,lambda:None)
    finally:supervise.ReferenceWatchdog,supervise.FollowPathBinding=prior_watchdog,prior_binding
    case=dict(completed=result.status==4 and len(reported)==1 and reported[0]['passed'],
              actual_watchdog_triggered_once=len(observed)==1,
              cancel_precedes_follow=events.index('NORMAL_CANCEL_ACK')<events.index('ONE_RECOVERY_FOLLOW_SENT'),
              original_goal_resumed=phase['normal_calls']==2,
              one_follow=events.count('ONE_RECOVERY_FOLLOW_SENT')==1,
              ownership_released_only_after_finish=node.committed_recovery is None,
              updated_constructor_source=reported[0]['proposal']['status']=='STATE_CONTINUOUS_RECOVERY_REFERENCE',
              full_cycle_revalidation='actual_goal_progress_lower_m' in reported[0]['install_effect'])
    rows.append(dict(index=index,checks=case,events=events,models=0,integrations=0))
    checks['case'+str(index)]=all(case.values())

for index in [0,1]:run_case(index)
checks['actual_new_modules_selected']=Path(supervise.construct.__code__.co_filename).resolve()==C/'state_reference.py' and Path(RecoveryTransaction.__module__ and sys.modules[RecoveryTransaction.__module__].__file__).resolve()==C/'transaction.py'
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
            action_peers_only=True,physical_authority=False,rows=rows)
(O/'SUPERVISOR_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
