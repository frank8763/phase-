"""Fresh production entries reject authority before any model or ROS import."""
import copy,importlib.abc,json,runpy,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v888_exact_lidar_dynamic'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
import authority as a
from handshake import ProtocolError
class Tests(unittest.TestCase):
    def setUp(self):
        self.task=json.loads((C/'TASKS.json').read_text())[1];self.freeze='SYNTHETIC_FREEZE_NO_LIVE_AUTHORITY'
        self.root=dict(models_authorized=True,user_requested_dynamic_stage=True,scope=a.SCOPE,started_unix=100.,deadline_unix=5500.,source_freeze_sha256=self.freeze)
        self.receipt=dict(self.root,run_id=self.task['run_id'],task_sha256=a.digest(self.task))
    def call(self,t=None,r=None,now=101.,root=None,closed=False,main_passed=False,preflight_passed=True):
        def read(p):
            if Path(p)==O/'AUTHORIZATION.json':return self.root if root is None else root
            if Path(p)==C/'TASKS.json':return json.loads((C/'TASKS.json').read_text())
            if Path(p)==O/'PREFLIGHTS.json':return dict(passed=preflight_passed)
            return dict(passed=main_passed)
        with patch.object(a,'read',side_effect=read),patch.object(a,'DEADLINE',5500.),patch.object(a,'validate_static_anchor',return_value=True),patch.object(Path,'exists',return_value=closed):return a.authorized(self.task if t is None else t,self.receipt if r is None else r,now,self.freeze)
    def test_registered_main_allowed_only_in_virtual_authority(self):self.assertEqual(self.call(),5500.)
    def test_template_is_not_live_authority(self):
        with self.assertRaisesRegex(ProtocolError,'MODELS_NOT_AUTHORIZED'):self.call(r=json.loads((C/'AUTHORIZATION_TEMPLATE.json').read_text()))
    def test_old_scope_rejected(self):
        with self.assertRaises(ProtocolError):self.call(r=dict(self.receipt,scope='V881_DAYTIME_OFFLINE'))
    def test_expired_rejected(self):
        with self.assertRaises(ProtocolError):self.call(now=5501.)
    def test_future_window_rejected(self):
        with self.assertRaises(ProtocolError):self.call(now=99.)
    def test_renewal_rejected(self):
        with self.assertRaises(ProtocolError):self.call(root=dict(self.root,deadline_unix=5501.))
    def test_nonfinite_window_rejected(self):
        with self.assertRaises(ProtocolError):self.call(root=dict(self.root,deadline_unix=float('nan')))
    def test_closed_window_rejected(self):
        with self.assertRaises(ProtocolError):self.call(closed=True)
    def test_changed_source_rejected(self):
        with self.assertRaises(ProtocolError):self.call(r=dict(self.receipt,source_freeze_sha256='changed'))
    def test_changed_task_rejected(self):
        task=dict(self.task,dynamic=False)
        with self.assertRaises(ProtocolError):self.call(t=task,r=dict(self.receipt,task_sha256=a.digest(task)))
    def test_unapproved_window_rejected(self):
        with self.assertRaises(ProtocolError):self.call(root=dict(self.root,user_requested_dynamic_stage=False))
    def test_changed_receipt_rejected(self):
        with self.assertRaises(ProtocolError):self.call(r=dict(self.receipt,task_sha256='changed'))
    def test_repeat_needs_successful_main(self):
        task=json.loads((C/'TASKS.json').read_text())[2];receipt=dict(self.receipt,run_id=task['run_id'],task_sha256=a.digest(task))
        with self.assertRaisesRegex(ProtocolError,'MAIN_NOT_PASSED'):self.call(t=task,r=receipt)
        self.assertEqual(self.call(t=task,r=receipt,main_passed=True),5500.)
    def test_fresh_worker_entries_and_invalid_run_do_not_import_models_or_ros(self):
        for name in ['native_worker.py','ros_worker.py']:
            code='''import importlib.abc,runpy,sys,json
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0]in ['mujoco','rclpy','vehicle','physical']:
   raise AssertionError('FORBIDDEN_IMPORT '+fullname)
sys.meta_path.insert(0,Block())
d=runpy.run_path(sys.argv[1],run_name='zero_entry_probe')
e=d['engine']
task=json.loads((d['C']/'TASKS.json').read_text())[0]
try:e.run(task,{},'NO_LIVE_AUTHORITY')
except RuntimeError as exc:assert str(exc)=='MODELS_NOT_AUTHORIZED',str(exc)
else:raise AssertionError('UNAUTHORIZED_RUN_NOT_REJECTED')
assert not any(x.split('.')[0]in ['mujoco','rclpy','vehicle','physical']for x in sys.modules)
print('FRESH_ENTRY_BLOCKED_BEFORE_PHYSICAL_OR_ROS')
'''
            p=subprocess.run([sys.executable,'-B','-c',code,str(C/name)],cwd=R,capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_dynamic_main_requires_true_t0(self):
        with self.assertRaisesRegex(ProtocolError,'DYNAMIC_T0_NOT_PASSED'):self.call(preflight_passed=False)
    def test_real_launcher_without_explicit_flag_cannot_start(self):
        p=subprocess.run([sys.executable,'-B',str(C/'run_validation.py')],cwd=R,capture_output=True,text=True,timeout=15)
        self.assertNotEqual(p.returncode,0);self.assertIn('DYNAMIC_STAGE_INSTRUCTION_REQUIRED',p.stderr);self.assertFalse((O/'AUTHORIZATION.json').exists())
def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    data=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),actual_models=0,native_integrations=0,real_ros_servers=0,live_authorization_created=False,root_window_started=False,scope='Pure authority plus genuine fresh-process entry tests, no MuJoCo/ROS imports')
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(data,indent=2)+'\n');return 0 if result.wasSuccessful()else 1
if __name__=='__main__':sys.exit(main())
