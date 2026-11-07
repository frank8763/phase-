"""Actual frozen backend loop with explicitly nonphysical dependencies and clock."""
import importlib.abc,json,sys,tempfile,unittest,hashlib
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];C=R/'experiments/v862_ready_static';O=R/'runs/v862_backend_qualification'
FORBIDDEN={'mujoco','torch','rclpy','vehicle','factory'}
class RejectModels(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]in FORBIDDEN:raise RuntimeError('FORBIDDEN_MODEL_OR_ROS_IMPORT '+fullname)
sys.meta_path.insert(0,RejectModels());sys.path.insert(0,str(C))
import native_backend as backend
import physical
from handshake import NODES,verify_sources,file_sha
class Clock:
    def __init__(self):self.mono=1000.;self.start=self.mono
    def monotonic(self):return self.mono
    def time(self):return 1000000.+self.mono-self.start
    def sleep(self,seconds):self.mono+=max(0.,seconds)
class FakeVehicle:
    def __init__(self,clock,fail_after=None):
        self.clock=clock;self.count=0;self.d=SimpleNamespace(time=0.);self.calls=[];self.fail_after=fail_after
    def scan(self):return dict(native_tick=self.count,time=self.d.time,ranges=[3.]*32,raw_lidar=[0.]*32,actor_xy=[123,456])
    def body(self):return [-4.,-2.,0.,0.,0.]
    def step(self,v,w,stale):
        self.count+=1;self.d.time=self.count*.01;self.calls.append(dict(at=self.clock.monotonic(),v=v,w=w,stale=stale))
        if self.fail_after==self.count:raise RuntimeError('SYNTHETIC_EXECUTOR_FAILURE_AFTER_CALL')
    def finish(self):
        return dict(actual_native=self.count,fully_recorded_native=self.count,root_guard_native_count=self.count,minimum_actual_clearance_m=.3,minimum_self_margin_m=.01,bad_contacts=0,final_translation_speed_m_s=0.,goal_distance_m=.1,final_body=self.body(),first_actor_detection=None,actual_travel_after_detection_m=0.,synthetic_fixture_not_physics=True)
class FakeDatagrams:
    def __init__(self,clock,run_id,mode):
        self.clock=clock;self.run_id=run_id;self.mode=mode;self.pending=deque();self.sent=[];self.arm_sent=False;self.command_sent=False;self.duplicate_sent=False;self.stop_sent=False;self.stop_at=None
    def bind(self,address):self.address=address
    def setblocking(self,value):pass
    def close(self):pass
    def recv(self,size):
        if not self.pending:raise BlockingIOError
        return json.dumps(self.pending.popleft()).encode()
    def arm(self):return dict(kind='arm',run_id=self.run_id,native_tick=0,sim_time=0.,states={n:3 for n in NODES},checked_at={n:self.clock.monotonic()for n in NODES},issued_at=self.clock.monotonic())
    def stop(self):
        self.pending.append(dict(kind='stop',run_id=self.run_id));self.stop_sent=True;self.stop_at=self.clock.monotonic()
    def sendto(self,data,peer):
        packet=json.loads(data);self.sent.append(packet)
        assert set(packet['scan'])=={'native_tick','time','ranges'}
        if packet['phase']=='WAITING'and not self.arm_sent:
            self.arm_sent=True
            if self.mode=='timeout':return
            if self.mode=='prearm_stop':self.stop();return
            if self.mode=='early_command':
                self.pending.append(dict(kind='command',run_id=self.run_id,sequence=1,issued_at=self.clock.monotonic(),v=.15,w=0.));return
            value=self.arm()
            if self.mode=='foreign_run':value['run_id']='other-run'
            if self.mode=='missing_node':del value['states'][NODES[-1]]
            self.pending.append(value)
        elif packet['phase']=='RUNNING':
            if not self.command_sent:
                self.pending.append(dict(kind='command',run_id=self.run_id,sequence=1,issued_at=self.clock.monotonic(),v=.15,w=.05));self.command_sent=True
            if self.mode=='normal'and packet['native_tick']>=5 and not self.duplicate_sent:
                self.pending.append(self.arm());self.duplicate_sent=True
            stop_tick=50 if self.mode=='expiry'else 10
            if self.mode in ['normal','expiry']and packet['native_tick']>=stop_tick and not self.stop_sent:self.stop()
ROWS=[]
def fixture(mode,fail_after=None):
    O.mkdir(exist_ok=True);clock=Clock();task=json.loads((C/'TASK_TEMPLATE.json').read_text());vehicle=FakeVehicle(clock,fail_after);transport=FakeDatagrams(clock,task['run_id'],mode);deadline=clock.time()+(40. if mode=='root_deadline'else 600.)
    # Directory is only a synthetic fixture under the frozen backend's allowed prefix.
    base=R/'runs/v858_nav2_verified';base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='zero_fixture_',dir=base)as directory:
        out=Path(directory);task.update(output=str(out),socket_dir=str(out.relative_to(R)))
        (out/'ROS_RESULT.json').write_text(json.dumps(dict(action_status=4,synthetic_fixture_not_real_ros=True)))
        def create(*args):
            if mode=='factory_failure':raise RuntimeError('SYNTHETIC_FACTORY_FAILURE')
            return vehicle
        def replay(*args):
            return dict(replay_native=vehicle.count,maximum_qpos_qvel_ctrl_mocap_error=0.,contact_mismatched_ticks=0,passed=True,synthetic_fixture_not_native_replay=True)
        with patch.object(backend,'authorized',return_value=deadline),patch.object(physical,'create_vehicle',side_effect=create),patch.object(physical,'replay',side_effect=replay),patch.object(backend.time,'time',side_effect=clock.time),patch.object(backend.time,'monotonic',side_effect=clock.monotonic),patch.object(backend.time,'sleep',side_effect=clock.sleep),patch.object(backend.socket,'socket',return_value=transport),patch.object(backend.os,'sched_getaffinity',return_value={0,1,2,3}),patch.object(backend.os,'sched_setaffinity'),patch.object(backend.signal,'signal'),patch.object(backend.signal,'setitimer'):
            result=backend.run(task,{},'SYNTHETIC_AUTHORITY_DEPENDENCY_ONLY')
        stored=json.loads((out/'RESULT.json').read_text());assert stored==result
    row=dict(mode=mode,status=result['status'],fake_executor_calls=vehicle.count,fake_replay_count=result['replay_native'],arm_time=result.get('armed_at'),virtual_elapsed_s=clock.monotonic()-clock.start,raw_synthetic_result=result,real_models=0,real_native_integrations=0,real_ros_servers=0)
    ROWS.append(row);return result,vehicle,transport,clock
class Tests(unittest.TestCase):
    def test_01_full_loop_duplicate_arm_and_complete_brake(self):
        result,v,wire,clock=fixture('normal');self.assertEqual(result['status'],'NATIVE_COMPLETE');self.assertTrue(result['passed']);self.assertTrue(wire.duplicate_sent);self.assertGreaterEqual(clock.monotonic()-wire.stop_at,2.);self.assertTrue(all(c['stale']and c['v']==c['w']==0. for c in v.calls[-199:]));self.assertEqual(len([e for e in result['startup_events']if e['event']=='ARMED_AT_T0']),1)
    def test_02_expiry_calls_brake_in_real_loop(self):
        result,v,wire,clock=fixture('expiry');self.assertEqual(result['status'],'NATIVE_COMPLETE');self.assertTrue(any(c['v']>.1 for c in v.calls));self.assertTrue(all(c['stale']for c in v.calls[30:]))
    def test_03_startup_timeout_never_steps(self):
        result,v,_,clock=fixture('timeout');self.assertEqual(v.count,0);self.assertEqual(result['actual_native'],0);self.assertIn('STARTUP_35S_DEADLINE',result['error']);self.assertGreaterEqual(clock.monotonic()-clock.start,35.)
    def test_04_stop_before_arm_never_steps(self):
        result,v,_,_=fixture('prearm_stop');self.assertEqual(result['status'],'PREARM_ABORT');self.assertEqual(v.count,0);self.assertFalse(result['passed'])
    def test_05_foreign_run_rejected(self):
        result,v,_,_=fixture('foreign_run');self.assertEqual(v.count,0);self.assertIn('FOREIGN_RUN',result['error'])
    def test_06_missing_active_node_rejected(self):
        result,v,_,_=fixture('missing_node');self.assertEqual(v.count,0);self.assertIn('INCOMPLETE_ACTIVE_SET',result['error'])
    def test_07_early_command_rejected(self):
        result,v,_,_=fixture('early_command');self.assertEqual(v.count,0);self.assertIn('COMMAND_BEFORE_ARM',result['error'])
    def test_08_factory_failure_preserves_unknown(self):
        result,v,_,_=fixture('factory_failure');self.assertIsNone(result['actual_native']);self.assertEqual(v.count,0);self.assertNotIn('environment_initialization_completed',result)
    def test_09_executor_failure_never_fills_replay_zero(self):
        result,v,_,_=fixture('executor_failure',fail_after=3);self.assertEqual(v.count,3);self.assertEqual(result['actual_native'],3);self.assertIsNone(result['replay_native']);self.assertFalse(result['passed'])
    def test_10_root_deadline_reserves_brake_and_replay(self):
        result,v,_,clock=fixture('root_deadline');self.assertEqual(result['status'],'NATIVE_COMPLETE');self.assertIn('ROOT_DEADLINE',result['stop_reason']);self.assertLess(clock.monotonic()-clock.start,20.);self.assertTrue(all(c['stale']for c in v.calls[-199:]))
def main():
    verify_sources(R,C/'SOURCE_FREEZE.json');assert not any(n.split('.')[0]in FORBIDDEN for n in sys.modules)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(verbosity=2).run(suite);verify_sources(R,C/'SOURCE_FREEZE.json')
    forbidden=[n for n in sys.modules if n.split('.')[0]in FORBIDDEN];record=dict(passed=result.wasSuccessful()and not forbidden,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),real_models=0,real_native_integrations=0,real_replay_integrations=0,real_ros_servers=0,navigation_actions=0,new24=0,original_source_unchanged=True,forbidden_modules_loaded=forbidden,synthetic_dependency_injection_only=True,real_authorization_created=False,real_window_started=False,cases=ROWS)
    (O/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');return 0 if record['passed']else 1
if __name__=='__main__':sys.exit(main())
