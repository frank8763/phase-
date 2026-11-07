"""Model-free regressions through actual production handshake and authority seams."""
import ast,copy,hashlib,importlib.abc,json,math,socket,sys,unittest
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v862_preparation'
FORBIDDEN=('mujoco','torch','rclpy','vehicle','factory')
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]in FORBIDDEN:raise RuntimeError('MODEL_OR_ROS_IMPORT_FORBIDDEN '+fullname)
blocker=NoModels();sys.meta_path.insert(0,blocker)
from handshake import Startup,NODES,ProtocolError,authorized,policy_packet,require_goal_allowed
import native_backend,ros_bridge,physical,launch,audit_result
class FakeVehicle:
    def __init__(self):self.count=0;self.d=SimpleNamespace(time=0.);self.calls=[]
    def step(self,v,w,stale):self.calls.append((v,w,stale));self.count+=1;self.d.time=self.count*.01
    def body(self):return [-4.,-2.,0.,0.,0.]
def arm(now=10.):return dict(kind='arm',run_id='fixture',native_tick=0,sim_time=0.,states={n:3 for n in NODES},checked_at={n:now for n in NODES},issued_at=now)
def command(sequence=1,now=10.):return dict(kind='command',run_id='fixture',sequence=sequence,issued_at=now,v=.15,w=.05)
class Tests(unittest.TestCase):
    def test_waiting_cannot_integrate(self):
        session=Startup('fixture');v=FakeVehicle()
        for _ in range(20):
            with self.assertRaises(ProtocolError):session.step(v,10.)
        self.assertEqual(v.count,0)
    def test_complete_arm_then_command_runs_production_step(self):
        s=Startup('fixture');v=FakeVehicle();s.receive(arm(),10.,0,0.);s.receive(command(),10.,0,0.);s.step(v,10.01)
        self.assertEqual(v.calls,[(.15,.05,False)]);self.assertEqual(v.count,1)
    def test_arm_missing_each_node_is_rejected(self):
        for name in NODES:
            p=arm();del p['states'][name];s=Startup('fixture')
            with self.assertRaises(ProtocolError):s.receive(p,10.,0,0.)
            self.assertIsNone(s.armed_at)
    def test_inactive_each_node_is_rejected(self):
        for name in NODES:
            p=arm();p['states'][name]=2
            with self.assertRaises(ProtocolError):Startup('fixture').receive(p,10.,0,0.)
    def test_stale_or_future_or_missing_proof_rejected(self):
        for value in [8.,11.,None,float('nan')]:
            p=arm();p['checked_at'][NODES[0]]=value
            with self.assertRaises(ProtocolError):Startup('fixture').receive(p,10.,0,0.)
    def test_nonzero_initial_state_rejected(self):
        for tick,sim in [(1,0.),(0,.01)]:
            with self.assertRaises(ProtocolError):Startup('fixture').receive(arm(),10.,tick,sim)
    def test_foreign_run_and_premature_command_rejected(self):
        p=arm();p['run_id']='old-run'
        with self.assertRaises(ProtocolError):Startup('fixture').receive(p,10.,0,0.)
        with self.assertRaises(ProtocolError):Startup('fixture').receive(command(),10.,0,0.)
    def test_duplicate_arm_never_restarts_clock(self):
        s=Startup('fixture');s.receive(arm(),10.,0,0.);s.receive(arm(12.),12.,200,2.)
        self.assertEqual(s.armed_at,10.);self.assertEqual(s.phase,'RUNNING')
    def test_old_or_nonfinite_or_reordered_command_rejected(self):
        for change in [dict(issued_at=9.),dict(issued_at=11.),dict(v=float('inf')),dict(w=float('nan'))]:
            s=Startup('fixture');s.receive(arm(),10.,0,0.);p=command();p.update(change)
            with self.assertRaises(ProtocolError):s.receive(p,10.,0,0.)
        s=Startup('fixture');s.receive(arm(),10.,0,0.);s.receive(command(),10.,0,0.)
        with self.assertRaises(ProtocolError):s.receive(command(),10.,0,0.)
    def test_command_expiry_and_stop_really_call_brake(self):
        s=Startup('fixture');v=FakeVehicle();s.receive(arm(),10.,0,0.);s.receive(command(),10.,0,0.);s.step(v,10.21)
        self.assertEqual(v.calls[-1],(0.,0.,True));s.receive(dict(kind='stop',run_id='fixture'),10.22,1,.01);s.step(v,10.22)
        self.assertEqual(v.calls[-1],(0.,0.,True))
    def test_prearm_stop_never_allows_a_step(self):
        s=Startup('fixture');v=FakeVehicle();s.receive(dict(kind='stop',run_id='fixture'),10.,0,0.)
        with self.assertRaises(ProtocolError):s.step(v,10.)
        self.assertEqual(v.count,0)
    def test_real_unix_datagram_roundtrip_uses_the_same_gate(self):
        a,b=socket.socketpair(socket.AF_UNIX,socket.SOCK_DGRAM)
        try:
            a.settimeout(.2);b.settimeout(.2);s=Startup('fixture');v=FakeVehicle()
            for packet in [arm(),command()]:a.send(json.dumps(packet).encode());s.receive(json.loads(b.recv(65536)),10.,v.count,v.d.time)
            s.step(v,10.01);self.assertEqual(v.count,1)
            a.send(json.dumps(arm(20.)).encode());s.receive(json.loads(b.recv(65536)),20.,1,.01);self.assertEqual(s.armed_at,10.)
        finally:a.close();b.close()
    def test_truth_fields_stripped_at_real_send_seam(self):
        scan=dict(native_tick=0,time=0.,ranges=[3.]*32,actor_xy=[99,99],raw_lidar=[0.]*32,goal_truth=[1,2])
        p=policy_packet('fixture',FakeVehicle(),scan,9.9,10.,'WAITING')
        self.assertEqual(set(p['scan']),{'native_tick','time','ranges'});self.assertNotIn('actor_xy',json.dumps(p));self.assertNotIn('raw_lidar',json.dumps(p));self.assertTrue(p['initial_snapshot'])
    def test_goal_requires_fresh_running_ack(self):
        base=dict(run_id='fixture',phase='RUNNING',sent_at=10.);require_goal_allowed(base,'fixture',10.1)
        for p in [None,dict(base,phase='WAITING'),dict(base,phase='STOPPING'),dict(base,run_id='old'),dict(base,sent_at=9.)]:
            with self.assertRaises(ProtocolError):require_goal_allowed(p,'fixture',10.1)
    def test_receipt_false_and_expired_denied_before_model_import(self):
        task=json.loads((C/'TASK_TEMPLATE.json').read_text());false=json.loads((C/'AUTHORIZATION_TEMPLATE.json').read_text())
        for entry in [native_backend.run,ros_bridge.run]:
            with self.assertRaisesRegex(ProtocolError,'MODELS_NOT_AUTHORIZED'):entry(task,false,'fixture-sha')
        receipt=dict(models_authorized=True,scope='ONE_STATIC_WEST_EAST',source_freeze_sha256='fixture-sha',run_id=task['run_id'],task_sha256=hashlib.sha256(json.dumps(task,sort_keys=True,separators=(',',':')).encode()).hexdigest(),started_unix=100.,deadline_unix=200.)
        self.assertEqual(authorized(task,receipt,110.,'fixture-sha'),200.)
        for changes in [dict(deadline_unix=105.),dict(source_freeze_sha256='wrong'),dict(task_sha256='wrong'),dict(run_id='wrong'),dict(started_unix=120.),dict(deadline_unix=float('nan'))]:
            with self.assertRaises(ProtocolError):authorized(task,dict(receipt,**changes),110.,'fixture-sha')
    def test_no_direct_vehicle_step_bypasses_production_gate(self):
        tree=ast.parse((C/'native_backend.py').read_text());steps=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='step']
        self.assertEqual(len(steps),1);self.assertIsInstance(steps[0].func.value,ast.Name);self.assertEqual(steps[0].func.value.id,'session')
    def test_launcher_denies_before_subprocess_and_runtime_access(self):
        from unittest.mock import patch
        with patch.object(sys,'argv',['launch.py',str(C/'AUTHORIZATION_TEMPLATE.json')]),patch.object(launch,'file_sha',return_value='fixture-sha'),patch.object(launch.subprocess,'Popen',side_effect=AssertionError('SUBPROCESS_BEFORE_AUTHORITY')):
            with self.assertRaisesRegex(ProtocolError,'MODELS_NOT_AUTHORIZED'):launch.main()
    def test_config_science_matches_original_v860(self):
        current=json.loads((C/'nav2_params.yaml').read_text());old=json.loads((R/'experiments/v860_nav2_prediction/physical_nav2_params.yaml').read_text())
        self.assertFalse(current['lifecycle_manager_navigation']['ros__parameters']['autostart'])
        current['lifecycle_manager_navigation']['ros__parameters']['autostart']=True
        current['map_server']['ros__parameters']['yaml_filename']=old['map_server']['ros__parameters']['yaml_filename']
        self.assertEqual(current,old)
    def test_missing_evidence_count_stays_unknown(self):
        import tempfile
        OUT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUT)as directory:
            value=audit_result.audit(dict(output=directory))
            self.assertFalse(value['passed']);self.assertIsNone(value['actual_native']);self.assertTrue(value['counts_may_be_unknown'])
    def test_prearm_zero_count_is_preserved_without_false_pass(self):
        import tempfile
        OUT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUT)as directory:
            Path(directory,'RESULT.json').write_text(json.dumps(dict(status='PREARM_ABORT',actual_native=0,replay_native=0)))
            value=audit_result.audit(dict(output=directory));self.assertFalse(value['passed']);self.assertEqual(value['actual_native'],0);self.assertFalse(value['counts_may_be_unknown'])
    def test_saved_arm_proof_independently_gates_audit(self):
        s=Startup('fixture');s.receive(arm(),10.,0,0.);n=dict(startup_events=s.events,armed_at=10.);r=dict(navigation_action_sent=True,goal_sent_at=10.1,cmd_vel_messages=2)
        self.assertTrue(all(audit_result.startup_checks(n,r).values()))
        bad=copy.deepcopy(n);bad['startup_events'][0]['states'][NODES[0]]=2;self.assertFalse(all(audit_result.startup_checks(bad,r).values()))
        bad=copy.deepcopy(n);bad['startup_events'][0]['checked_at'][NODES[0]]=8.;self.assertFalse(all(audit_result.startup_checks(bad,r).values()))
        self.assertFalse(all(audit_result.startup_checks(n,dict(r,goal_sent_at=9.)).values()))
    def test_corrupt_result_is_failed_and_never_zero_filled(self):
        import tempfile
        OUT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUT)as directory:
            Path(directory,'RESULT.json').write_text('{interrupted partial JSON')
            result=audit_result.audit(dict(output=directory));self.assertFalse(result['passed']);self.assertIsNone(result['actual_native']);self.assertTrue(result['counts_may_be_unknown'])
def main():
    OUT.mkdir(exist_ok=True);before={name for name in sys.modules if name.split('.')[0]in FORBIDDEN};suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(verbosity=2).run(suite)
    after={name for name in sys.modules if name.split('.')[0]in FORBIDDEN};require=not before and not after
    record=dict(passed=result.wasSuccessful()and require,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),forbidden_modules_loaded=sorted(after),physical_vehicle_models=0,native_integrations=0,ros_servers_started=0,navigation_actions=0,fake_actuator_only=True,real_unix_datagram_qualified=True,scope='Protocol/source qualification only; no physical or navigation acceptance')
    (OUT/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');return 0 if record['passed']else 1
if __name__=='__main__':sys.exit(main())
