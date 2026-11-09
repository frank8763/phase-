"""Real saved-failure and production transaction/receive seams; zero vehicle models."""
import copy,gzip,importlib.abc,json,sys,threading,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v909_timed_command_contract'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('FORBIDDEN_MODEL_IMPORT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from command_tube import admit,nominal
sys.path.insert(0,str(C))
from native_contract import Startup
from motion_publisher import MotionPublisher
from support_envelope import SupportEnvelope
from exact_lidar import get_lidar_features
known=json.loads((O/'saved/SETUP.json').read_text())['known']
events=json.loads((O/'saved/REFUGE_SUPERVISION.json').read_text())['events']
commands=json.loads((O/'saved/BODY_COMMANDS.json').read_text())
checks={};witnesses=[]
for e in events:
    if e['event']!='REFUGE_REQUEST':continue
    s=copy.deepcopy(e['source']);p=dict(native_tick=e['native_tick'],body=e['body'],sent_at=100.,body_measured_at=100.)
    v,w=commands[e['native_tick']-1][1:3]
    proof=admit(p,s,v,w,known,100.);witnesses.append(proof)
checks['three_actual_old_retreat_poses_have_finite_moving_permission']=len(witnesses)==3 and all(x['passed'] for x in witnesses)
bad=next(x for x in events if x['source']['source_native_tick']>x['native_tick'])
try:admit(dict(native_tick=bad['native_tick'],body=bad['body'],sent_at=100.,body_measured_at=100.),bad['source'],0.,0.,known,100.)
except AssertionError as e:checks['actual_8985_8986_causal_violation_rejected']='FUTURE' in str(e)
else:checks['actual_8985_8986_causal_violation_rejected']=False
e=next(x for x in events if x['event']=='REFUGE_REQUEST');p=dict(native_tick=e['native_tick'],body=e['body'],sent_at=100.,body_measured_at=100.);s=e['source']
for name,pp,ss,v,w,now in [
    ('stale_body',p,s,0.,0.,100.051),('speed_outside_qualification',p,s,.11,0.,100.),
    ('curvature_outside_qualification',p,s,.1,.1,100.),('nonfinite',p,s,float('nan'),0.,100.),
    ('stale_scan',p,dict(s,source_age_s=.201),0.,0.,100.)]:
    try:admit(pp,ss,v,w,known,now)
    except AssertionError:checks[name+'_rejected']=True
    else:checks[name+'_rejected']=False
from support_envelope import NORMALS
colliding=dict(s,support_bounds=(NORMALS@np.asarray(p['body'][:2])).tolist())
checks['obstacle_intersecting_body_rejected']=not admit(p,colliding,0.,0.,known,100.)['passed']
check_static=dict(p,body=[0.,3.25,0.,0.,0.])
checks['known_wall_rejected']=not admit(check_static,dict(s,support_bounds=None),0.,0.,known,100.)['passed']
times=np.linspace(0.,2.2,221);q=nominal([0,0,0,0,0],.1,0.,times)
checks['nominal_commits_only_200ms']=np.max(abs(q[:,0]-.1*np.minimum(times,.2)))<1e-12 and np.ptp(q[20:,0])==0
session=Startup('qualification');session.phase='RUNNING';session.armed_at=99.
pr=admit(p,s,0.,0.,known,100.)
packet=dict(kind='command',run_id='qualification',sequence=1,issued_at=100.,v=0.,w=0.,tube=pr)
session.receive(packet,100.01,p['native_tick']+1,0.)
checks['native_accepts_matching_qualified_command']=session.command==packet
for name,mutated,now in [('missing_proof',dict(packet,tube={}),100.01),('changed_command',dict(packet,v=.01),100.01),('late_delivery',packet,100.051),('future_source',dict(packet,tube=dict(pr,body_native_tick=999999)),100.01)]:
    fresh=Startup('qualification');fresh.phase='RUNNING';fresh.armed_at=99.
    try:fresh.receive(mutated,now,p['native_tick']+1,0.)
    except (AssertionError,RuntimeError,ValueError,KeyError):checks[name+'_native_rejected']=True
    else:checks[name+'_native_rejected']=False
# Actual production publisher, source tracker and planner snapshot under concurrent access.
obj=MotionPublisher.__new__(MotionPublisher);obj.lock=threading.RLock();obj.tracker=SupportEnvelope(known,get_lidar_features);obj.observations=[];obj.known_packets=0;obj.running=False
scans=json.loads(gzip.decompress((O/'saved/SENSORS.json.gz').read_bytes()))
with patch('time.monotonic',return_value=100.):
    for scan in scans:
        if scan['native_tick']>8986:break
        obj.observe(dict(scan=scan,phase='RUNNING',native_tick=scan['native_tick'],body=[*scan['xy'],scan['yaw'],0.,0.],scan_measured_at=100.,sent_at=100.,body_measured_at=100.))
    ready=threading.Event();release=threading.Event();done=threading.Event();pairs=[]
    def writer():
        with obj.lock:ready.set();assert release.wait(2.)
    def reader():pairs.append(obj.planning_snapshot());done.set()
    w=threading.Thread(target=writer);w.start();assert ready.wait(2.)
    r=threading.Thread(target=reader);r.start();checks['planner_reader_waits_for_observation_transaction']=not done.wait(.03)
    release.set();w.join(2.);r.join(2.);assert len(pairs)==1
    _,source,body=pairs[0]
    checks['production_planner_pair_is_causal']=source['source_native_tick']==body['native_tick']==8986
    body['body'][0]+=999
    checks['planner_cannot_mutate_store']=obj.decision_snapshot()[0]['body'][0]!=body['body'][0]
checks={k:bool(v) for k,v in checks.items()}
report=dict(passed=all(checks.values()),checks=checks,saved_failure_witnesses=witnesses,models=0,integrations=0,
            scope='Finite local command witnesses and production dataflow, not complete route reachability or dynamic acceptance')
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));assert report['passed']
