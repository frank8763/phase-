"""Production causal publisher/tube and independent saved evidence; zero models."""
import ast,copy,gzip,importlib.abc,json,math,shutil,sys,threading,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v911_periodic_causal_navigation';S=R/'runs/v910_corridor_diagnosis/saved'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from periodic_support import PeriodicSupport,bounds_from_vertices,swept_bounds,Polytope
from command_tube import admit,nominal
sys.path.insert(0,str(C));from motion_publisher import MotionPublisher
from support_envelope import SupportEnvelope
from exact_lidar import get_lidar_features
known=json.loads((S/'physics/SETUP.json').read_text())['known']
old=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()))[-1]
obj=MotionPublisher.__new__(MotionPublisher);obj.lock=threading.RLock();obj.tracker=SupportEnvelope(known,get_lidar_features);obj.periodic=PeriodicSupport();obj.observations=[];obj.known_packets=0;obj.running=True
scans=json.loads(gzip.decompress((S/'MOTION_ENVELOPE.json.gz').read_bytes()))['observations']
with patch('time.monotonic',return_value=100.):
 for scan in scans:
  if scan['native_tick']>old['source']['source_native_tick']:break
  packet=dict(scan=scan,phase='RUNNING',native_tick=scan['native_tick'],body=list(old['packet']['body']),scan_measured_at=100.,body_measured_at=100.,sent_at=100.)
  obj.observe(packet)
 packet,source=obj.decision_snapshot();dynamic,planning,body=obj.planning_snapshot()
proof=admit(packet,source,.1,0.,known,100.);checks=dict(saved_failed_forward_now_admitted=proof['passed'],same_causal_body_source=packet['native_tick']==source['source_native_tick']==6461,no_future_periodic_data=source['periodic']['source_tick']<=source['source_native_tick'],published_same_enclosure=np.allclose(planning['forecast_support'],obj.contract_forecast(obj.tracker.when)),all_python_parses=all(ast.parse(p.read_text())for p in C.glob('*.py')))
for name,pp,ss,now in [('stale_body',packet,source,100.051),('future_scan',packet,dict(source,source_native_tick=6462),100.),('wrong_period',packet,dict(source,periodic=dict(source['periodic'],omega=.33)),100.),('future_coefficients',packet,dict(source,periodic=dict(source['periodic'],source_tick=6462)),100.)]:
 try:admit(pp,ss,.1,0.,known,now)
 except (AssertionError,ValueError):checks[name+'_rejected']=True
 else:checks[name+'_rejected']=False
# Independent dense interval evaluation, including intervals spanning more than a period.
prior=source['periodic'];intervals=[(0.,.1),(59.,62.),(64.,66.5),(0.,50.)]
checks['swept_extrema_enclose_dense_times']=all(np.all(swept_bounds(prior['vertices'],a,b)>=bounds_from_vertices(prior['vertices'],np.linspace(a,b,10001)).max(axis=0)-1e-10)for a,b in intervals)
# Fixed positive/negative coefficient constraints. Finite deterministic random set,
# no model, no task or phase selection. Tests the clipping algorithm itself.
rng=np.random.default_rng(911);synthetic=0
for case in range(80):
 coefficients=rng.uniform([-4,-.25,-.25],[4,.25,.25]);poly=Polytope()
 for t in np.linspace(0,30,20):
  n=np.array([1,np.sin(.32*t),np.cos(.32*t)]);z=n@coefficients;poly.clip(n,z+rng.uniform(.01,.1));poly.clip(-n,-z+rng.uniform(.01,.1))
  directions=rng.normal(size=(25,3));synthetic+=len(directions)
  assert np.all(directions@coefficients<=np.max(directions@poly.v.T,axis=1)+1e-8)
checks['synthetic_coefficient_coverage_40000']=synthetic==40000
try:poly.clip(np.array([1.,0.,0.]),-9.)
except ValueError:checks['inconsistent_prior_rejected']=True
else:checks['inconsistent_prior_rejected']=False
# Actual loader selections, not name-only source inspection.
sys.path.insert(0,str(C));import native_worker
sys.path.insert(0,str(C));import ros_worker
checks['native_selects_candidate']=native_worker.engine.C==C
checks['ros_selects_candidate']=ros_worker.engine.C==C
checks['native_command_monitor_unchanged']=(C/'native_contract.py').read_bytes()==(R/'experiments/v909_timed_command_contract/native_contract.py').read_bytes()
checks['two_original_tasks_only']=len(json.loads((C/'TASKS.json').read_text()))==2
checks['old18_response_all_passed']=json.loads((O/'PRIOR_RESPONSE_QUALIFICATION.json').read_text())['all18_qualified']
# Full native saved body/source checks under independent tube integration formula.
fixture=O/'audit_fixture';(fixture/'physics').mkdir(parents=True,exist_ok=True)
for n in ['NATIVE_TRACE.npz','SETUP.json']:shutil.copyfile(S/'physics'/n,fixture/'physics'/n)
shutil.copyfile(S/'MOTION_ENVELOPE.json.gz',fixture/'MOTION_ENVELOPE.json.gz')
(fixture/'ROS_RESULT.json').write_text('{"synthetic_status_only":true}')
(fixture/'RESULT.json').write_text('{"status":"NATIVE_COMPLETE","synthetic_status_only":true}')
checks['host_rebuild_matches_original_ros_support_to_1e_10']=bool(np.max(abs(np.asarray(source['support_bounds'])-old['source']['support_bounds']))<1e-10)
source['support_bounds']=old['source']['support_bounds']
packet['body']=old['packet']['body'];proof=admit(packet,source,.1,0.,known,100.);row=dict(packet=packet,source=source,wanted=[.1,0.],proof=proof)
sys.path.insert(0,str(C));from tube_audit import audit_tubes
def audit(r):
 with gzip.open(fixture/'COMMAND_TUBES.json.gz','wt')as f:json.dump(r,f)
 return audit_tubes(fixture)
checks['independent_dense_saved_tube_passes']=audit([row])['passed']
for key in ['body','support','threshold','command']:
 bad=copy.deepcopy(row)
 if key=='body':bad['packet']['body'][0]+=.01
 if key=='support':bad['source']['support_bounds'][0]+=.01
 if key=='threshold':bad['proof']['static_lower_m']=.149
 if key=='command':bad['proof']['v']=.2
 checks['audit_rejects_'+key]=not audit([bad])['passed']
checks={k:bool(v)for k,v in checks.items()};result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,finite_declared_periodic_class_only=True,synthetic_status_fixture_not_physical_result=True,saved_terminal_forward_proof=proof)
for n in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json']:(O/n).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks=checks)));assert result['passed']
