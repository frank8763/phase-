"""Deterministic old-race reproduction and real tracker transaction qualification."""
import copy,gzip,importlib.abc,json,sys,threading,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v908_causal_progress_contract'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle','factory'}:raise AssertionError('FORBIDDEN_MODEL_IMPORT')
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from coherent_observation import CoherentMotionPublisher
from support_envelope import SupportEnvelope
from exact_lidar import get_lidar_features
root=R/'runs/v858_nav2_verified/v907/main_we';saved=json.loads((root/'REFUGE_SUPERVISION.json').read_text());bad=next(e for e in saved['events']if e['source']['source_native_tick']>e['native_tick']);checks={'actual_saved_mixed_snapshot_red':bad['native_tick']==8985 and bad['source']['source_native_tick']==8986}
scans=json.loads(gzip.decompress((root/'physics/SENSORS.json.gz').read_bytes()));known=json.loads((root/'physics/SETUP.json').read_text())['known']
obj=CoherentMotionPublisher.__new__(CoherentMotionPublisher);obj.lock=threading.RLock();obj.tracker=SupportEnvelope(known,get_lidar_features);obj.observations=[];obj.known_packets=0;obj.scan_monotonic=None;obj.running=False
packets=[]
for s in scans:
 if s['native_tick']>8991:break
 p=dict(scan=s,phase='RUNNING',native_tick=s['native_tick'],body=[*s['xy'],s['yaw'],0.,0.],scan_measured_at=100.,sent_at=100.)
 packets.append(p)
 with patch('time.monotonic',return_value=100.):obj.observe(p)
 if s['native_tick']==8981:break
old_packet=packets[-1]
next_scan=next(s for s in scans if s['native_tick']==8986);new_packet=dict(scan=next_scan,phase='RUNNING',native_tick=8986,body=[*next_scan['xy'],next_scan['yaw'],0.,0.],scan_measured_at=100.,sent_at=100.)
ready=threading.Event();release=threading.Event();reader_done=threading.Event();result=[]
def writer():
 with obj.lock:
  obj.observe(new_packet);ready.set();assert release.wait(2.)
def reader():
 result.append(obj.decision_snapshot());reader_done.set()
with patch('time.monotonic',return_value=100.):
 w=threading.Thread(target=writer);w.start();assert ready.wait(2.)
 t=threading.Thread(target=reader);t.start();checks['reader_blocked_during_writer_transaction']=not reader_done.wait(.03)
 # Reproduce old supervisor read order: saved old packet then lock for new source.
 checks['old_two_read_order_is_inconsistent']=old_packet['native_tick']<obj.tracker.latest['native_tick']
 release.set();w.join(2.);t.join(2.);assert not w.is_alive()and not t.is_alive()
 p,s=result[0];checks['new_pair_same_native_measurement']=p['native_tick']==s['source_native_tick']==8986
 checks['exact_original_tracker_values']=np.array_equal(s['support_bounds'],obj.tracker.support)
 p['body'][0]+=999;s['support_bounds'][0]+=999;p2,s2=obj.decision_snapshot()
 checks['consumer_mutation_cannot_modify_store']=p2['body'][0]!=p['body'][0]and s2['support_bounds'][0]!=s['support_bounds'][0]
with patch('time.monotonic',return_value=100.21):
 try:obj.decision_snapshot()
 except RuntimeError:checks['stale_pair_rejected']=True
 else:checks['stale_pair_rejected']=False
proof=dict(passed=all(checks.values()),checks=checks,original_failure_tick=8985,source_tick=8986,models=0,integrations=0,scope='Actual MotionPublisher.observe and actual causal tracker with real saved scans; deterministic concurrency seam; no navigation or repair of old V907 outcome.')
(O/'SNAPSHOT_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');(R/'records/nav2_v908_20261109/SNAPSHOT_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof));assert proof['passed']
