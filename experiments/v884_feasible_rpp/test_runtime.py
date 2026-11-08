"""Actual new backend loop with virtual clock and explicit fake vehicle; zero MuJoCo/ROS."""
import gc,importlib.util,json,signal,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v884_feasible_rpp'
spec=importlib.util.spec_from_file_location('original_loop_fixture',R/'experiments/v862_backend_qualification/loop_fixture.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
sys.path.insert(0,str(R/'experiments/v882_runtime_evidence_repair'));import native_loop as backend

ROWS=[]
def fixture(fault=None,where='step',delay=.12,clock_budget=600.,mode='normal',replay_error=False,save_error=False,incomplete=False):
    clock=q.Clock();task=json.loads((q.C/'TASK_TEMPLATE.json').read_text());vehicle=q.FakeVehicle(clock);wire=q.FakeDatagrams(clock,task['run_id'],mode);injected=False;handlers={};replay_calls=[];stop_flag=[]
    def inject(stage):
        nonlocal injected
        if injected or vehicle.count<5:return
        if stage==where and fault in ['lag','executor','terminate','deadline']:
            injected=True
            if fault=='lag':clock.mono+=delay
            elif fault=='deadline':clock.mono+=clock_budget-5;raise RuntimeError('SYNTHETIC_STEP_FAILED_NEAR_DEADLINE')
            elif fault=='executor':raise RuntimeError('SYNTHETIC_STEP_FAILURE')
            else:handlers[signal.SIGTERM](signal.SIGTERM,None)
    original_step=vehicle.step;original_scan=vehicle.scan;original_finish=vehicle.finish
    def step(*args):original_step(*args);inject('step')
    def scan():result=original_scan();inject('scan');return result
    def finish():
        if save_error:raise OSError('SYNTHETIC_EVIDENCE_WRITE_ERROR')
        result=original_finish()
        if incomplete:result['fully_recorded_native']=max(0,vehicle.count-1)
        return result
    if fault=='native_interrupted':
        def interrupted_native():raise InterruptedError('SYNTHETIC_NATIVE_C_CALL_INTERRUPTED')
        vehicle.native=interrupted_native
        def interrupted_step(*args):original_step(*args);vehicle.native()
        vehicle.step=interrupted_step
    else:vehicle.step=step
    vehicle.scan=scan;vehicle.finish=finish
    def create(*args):
        if fault=='factory':raise RuntimeError('SYNTHETIC_FACTORY_FAILURE')
        return vehicle
    def replay(instance,deadline,out):
        replay_calls.append(instance.count)
        if replay_error:
            (out/'REPLAY_PROGRESS.json').write_text('{"executed_replay_native":2}');raise TimeoutError('SYNTHETIC_REPLAY_INTERRUPTION')
        return dict(replay_native=instance.count,maximum_qpos_qvel_ctrl_mocap_error=0.,contact_mismatched_ticks=0,passed=fault!='replay_mismatch')
    def sleep(seconds):clock.sleep(seconds);inject('pacing')
    def register(sig,handler):old=handlers.get(sig,signal.SIG_DFL);handlers[sig]=handler;return old
    base=R/'runs/v858_nav2_verified';base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v884_zero_',dir=base)as directory:
        out=Path(directory);(out/'physics').mkdir();task.update(output=str(out),socket_dir=str(out.relative_to(R)));(out/'ROS_RESULT.json').write_text('{"action_status":4,"synthetic_fixture_not_real_ros":true}')
        deadline=clock.time()+clock_budget
        with patch.object(backend,'C',q.C),patch.object(backend,'authorized',return_value=deadline),patch.object(q.physical,'create_vehicle',side_effect=create),patch.object(q.physical,'replay',side_effect=replay),patch.object(backend.time,'time',side_effect=clock.time),patch.object(backend.time,'monotonic',side_effect=clock.monotonic),patch.object(backend.time,'sleep',side_effect=sleep),patch.object(backend.socket,'socket',return_value=wire),patch.object(backend.os,'sched_getaffinity',return_value={0,1,2,3}),patch.object(backend.os,'sched_setaffinity'),patch.object(backend.signal,'signal',side_effect=register),patch.object(backend.signal,'setitimer'),patch('runtime_timing.gc.collect'):
            result=backend.run(task,{},'VIRTUAL_AUTHORITY_ONLY')
        assert json.loads((out/'RESULT.json').read_text())==result
        profile=json.loads((out/'RUNTIME_TIMING.json').read_text());assert profile==result['timing_profile']
    ROWS.append(dict(fault=fault,where=where,status=result['status'],fake_executed=vehicle.count,fake_replayed=result['replay_native'],model_initializations=0,model_integrations=0,ros_servers=0,maximum_lag_s=result['maximum_wall_lag_s'],replay_status=result.get('replay_status')))
    return result,vehicle,wire,clock,profile,replay_calls

class Tests(unittest.TestCase):
    def test_normal_loop_remains_successful(self):
        r,v,w,c,p,replay=fixture();self.assertTrue(r['passed']);self.assertEqual(r['status'],'NATIVE_COMPLETE');self.assertEqual(replay,[v.count]);self.assertGreaterEqual(c.monotonic()-w.stop_at,2.);self.assertTrue(all(x['stale']for x in v.calls[-199:]));self.assertEqual(r['replay_native'],v.count)
    def test_virtual_normal_control_schedule_matches_original(self):
        old,v0,_,_=q.fixture('normal');new,v1,_,_,_,_=fixture();self.assertEqual(v0.count,v1.count);self.assertEqual(v0.calls,v1.calls);self.assertEqual(old['passed'],new['passed'])
    def test_lag_in_step_keeps_failure_and_complete_prefix_replay(self):
        r,v,_,_,p,calls=fixture('lag');self.assertFalse(r['passed']);self.assertIn('PHYSICS_WALL_LAG_OVER_100MS',r['error']);self.assertEqual(v.count,5);self.assertEqual(calls,[5]);self.assertEqual(r['replay_native'],5);self.assertGreater(p['overrun']['lag_s'],.1);self.assertAlmostEqual(p['summaries']['step_and_native_safety']['maximum_s'],.12,8)
    def test_lag_in_scan_attributed_to_scan(self):
        r,v,_,_,p,calls=fixture('lag',where='scan');self.assertIn('PHYSICS_WALL_LAG_OVER_100MS',r['error']);self.assertGreaterEqual(p['summaries']['scan']['maximum_s'],.119);self.assertEqual(r['replay_native'],v.count);self.assertFalse(r['passed'])
    def test_subthreshold_delay_does_not_weaken_original_gate(self):
        r,v,_,_,p,_=fixture('lag',where='pacing',delay=.099);self.assertEqual(r['status'],'NATIVE_COMPLETE');self.assertLessEqual(p['maximum_wall_lag_s'],.1)
    def test_overthreshold_delay_always_fails(self):
        r,_,_,_,_,_=fixture('lag',where='pacing',delay=.101);self.assertIn('PHYSICS_WALL_LAG_OVER_100MS',r['error']);self.assertFalse(r['passed'])
    def test_step_exception_still_replays_recorded_prefix(self):
        r,v,_,_,_,calls=fixture('executor');self.assertEqual(v.count,5);self.assertIn('SYNTHETIC_STEP_FAILURE',r['error']);self.assertEqual(calls,[5]);self.assertEqual(r['replay_native'],5);self.assertFalse(r['passed'])
    def test_interrupted_replay_preserves_unknown_total_and_progress(self):
        r,v,_,_,_,_=fixture('lag',replay_error=True);self.assertIsNone(r['replay_native']);self.assertEqual(r['replay_completed_native_lower_bound'],2);self.assertIn('PHYSICS_WALL_LAG_OVER_100MS',r['error']);self.assertEqual(r['secondary_errors'][0]['stage'],'own_prefix_replay');self.assertFalse(r['passed'])
    def test_deadline_never_reopens_for_replay(self):
        r,v,_,_,_,calls=fixture('deadline',clock_budget=40.);self.assertEqual(v.count,5);self.assertEqual(calls,[]);self.assertIsNone(r['replay_native']);self.assertEqual(r['replay_status'],'NOT_STARTED_ROOT_DEADLINE_RESERVE')
    def test_incomplete_native_record_never_claims_full_replay(self):
        r,v,_,_,_,calls=fixture('executor',incomplete=True);self.assertEqual(calls,[]);self.assertIsNone(r['replay_native']);self.assertEqual(r['replay_status'],'INCOMPLETE_NATIVE_RECORD_NO_FULL_REPLAY_CLAIM')
    def test_serialization_error_never_masks_actual_count(self):
        r,v,_,_,_,calls=fixture('executor',save_error=True);self.assertEqual(r['actual_native'],5);self.assertFalse(r['evidence_save_complete']);self.assertIn('SYNTHETIC_STEP_FAILURE',r['error']);self.assertEqual(r['secondary_errors'][0]['stage'],'evidence_save');self.assertEqual(calls,[]);self.assertFalse(r['passed'])
    def test_factory_failure_keeps_unknown_actual_count(self):
        r,v,_,_,_,calls=fixture('factory');self.assertIsNone(r['actual_native']);self.assertEqual(calls,[]);self.assertFalse(r['passed'])
    def test_interrupted_native_call_does_not_invent_exact_total(self):
        r,v,_,_,_,calls=fixture('native_interrupted');self.assertIsNone(r['actual_native']);self.assertEqual(calls,[]);self.assertEqual(r['native_api_calls_completed'],0);self.assertEqual(r['actual_native_completed_lower_bound'],v.count);self.assertFalse(r['passed'])
    def test_prearm_stop_never_executes(self):
        r,v,_,_,_,calls=fixture(mode='prearm_stop');self.assertEqual(v.count,0);self.assertEqual(calls,[]);self.assertEqual(r['status'],'PREARM_ABORT')
    def test_prearm_timeout_never_executes(self):
        r,v,_,_,_,calls=fixture(mode='timeout');self.assertEqual(v.count,0);self.assertEqual(calls,[]);self.assertIn('STARTUP_35S_DEADLINE',r['error'])
    def test_sigterm_records_error_and_does_not_restart_navigation(self):
        r,v,_,_,_,calls=fixture('terminate');self.assertEqual(v.count,5);self.assertIn('EXTERNAL_TERMINATION_STOP',r['error']);self.assertEqual(calls,[5]);self.assertFalse(r['passed'])
    def test_root_deadline_preserves_original_brake_before_stop(self):
        r,v,w,c,_,_=fixture(mode='root_deadline',clock_budget=40.);self.assertEqual(r['status'],'NATIVE_COMPLETE');self.assertLess(c.monotonic()-c.start,20.);self.assertTrue(all(x['stale']for x in v.calls[-199:]))
    def test_gc_flag_restored_on_success_and_failure(self):
        before=gc.isenabled()
        try:
            gc.enable();fixture('lag');self.assertTrue(gc.isenabled());fixture();self.assertTrue(gc.isenabled());gc.disable();fixture('executor');self.assertFalse(gc.isenabled())
        finally:
            if before:gc.enable()
            else:gc.disable()
    def test_replay_mismatch_is_not_success(self):
        r,_,_,_,_,_=fixture('replay_mismatch');self.assertEqual(r['status'],'REPLAY_MISMATCH');self.assertFalse(r['passed'])

def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));record=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),models=0,integrations=0,real_ros_servers=0,old_model_window_reopened=False,cases=ROWS,scope='Actual new runtime loop and original-normal-loop equivalence under explicit nonphysical dependencies; not real timing/model validation')
    (O/'ZERO_QUALIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');return 0 if result.wasSuccessful()else 1
if __name__=='__main__':sys.exit(main())
