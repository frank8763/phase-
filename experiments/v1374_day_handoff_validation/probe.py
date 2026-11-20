"""Fixed saved-input constructive probes. Metadata/nominal kinematics, no models."""
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main'

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('PROBE_MODELS_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np

def load(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from observed_route import geometry
from causal_occupancy import base
from segments import validate

def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda z:z.item() if isinstance(z,np.generic) else z.tolist())+'\n')

def saved():
    queue=[];results={};journal=read(RAW/'APPLIED_JOURNAL.json')
    forecasts={e['native_tick']:e for e in read(RAW/'FORECAST_RECORDS.json')}
    for e in read(RAW/'SEGMENT_RECORDS.json'):
        if e['event']=='INSTALL_ORDERED_ROUTE':queue=e['segments'][1:]
        elif e['event']=='CUSP_NEXT_SEGMENT_CHECK':
            if e['native_tick'] in [9390,32210]:results[e['native_tick']]=dict(body=e['body'],segment=queue[0],forecast=forecasts[e['native_tick']],memory=journal[e['native_tick']]['last_ctrl'])
            queue=queue[1:] if e['accepted'] else []
    return results,read(RAW/'physics/SETUP.json')['known']

def center_steering(memory):
    # Same inverse Ackermann geometry; actual axle/track from saved qualified source.
    # Geometry from V1365 qualify_coupled.initial_steering: .6m axle/.54m track.
    L=.6;h=.27
    left=math.tan(memory[0])/(L+h*math.tan(memory[0]));right=math.tan(memory[1])/(L-h*math.tan(memory[1]))
    assert abs(left-right)<=1e-8,'SAVED_ACKERMANN_PAIR_NOT_COORDINATED'
    return math.atan(L*(left+right)/2)

def capture(body,delta,candidate):
    yaw=body[2];pose=np.array([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw]);rows=[];clock=0.
    speed=0.;labels=[]
    for gear,curvature,distance in [(-1,candidate['reverse_curvature_m_inv'],candidate['reverse_nominal_distance_m']),(1,candidate['forward_curvature_m_inv'],candidate['forward_nominal_distance_m'])]:
        # Complete accel/cruise/brake and two-second hold, including actual saved
        # initial steering and continuous steering slew. Explicitly NOMINAL.
        target=math.atan(.6*curvature);cruise=max(0.,(distance-.15)/.1);end=1.+cruise+2.+2.
        for i in range(round(end/.01)):
            t=(i+1)*.01
            desired=gear*(.1*t if t<=1. else .1 if t<=1.+cruise else max(0.,.1-.05*(t-1.-cruise)))
            next_delta=delta+float(np.clip(target-delta,-.006,.006)) if abs(desired)>0. else delta
            travel=.005*(speed+desired);k=math.tan((delta+next_delta)/2)/.6;heading=pose[2]+travel*k
            if abs(k)>1e-10:pose[:2]+=[(math.sin(heading)-math.sin(pose[2]))/k,-(math.cos(heading)-math.cos(pose[2]))/k]
            else:pose[:2]+=travel*np.array([math.cos(pose[2]),math.sin(pose[2])])
            pose[2]=heading;clock+=.01;speed=desired;delta=next_delta;rows.append([*pose,clock,speed,delta]);labels.append(gear)
    return np.asarray(rows),labels

def field(known,ball=None):
    circles=list(known['known_circles'])
    if ball is not None:circles.append([*ball[0],ball[1]])
    return SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(circles),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))

def periodic_prefix(tick):
    support=base.periodic.PeriodicSupport();seen=0
    for e in read(RAW/'CAUSAL_OBSERVATIONS.json'):
        if e['native_tick']>tick:break
        bounds=base.NORMALS@np.array(e['point'])+.24
        support.update(e['sim_time'],e['native_tick'],bounds.tolist());seen+=1
    assert support.source_tick<=tick
    return support,seen

def interval_ball(vertices,start,end):
    b=base.swept.swept_bounds(vertices,start,end);lower=-b[[8,12]];upper=b[[0,4]]
    return (lower+upper)/2,float(np.linalg.norm((upper-lower)/2))+.10

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('BOUNDED_ZERO_MODEL_PROBE_180S')));signal.alarm(180)
    begin=time.monotonic();states,known=saved();candidate=read(C/'CANDIDATES.json')['candidates'][0]
    a=states[9390];delta=center_steering(a['memory']);trajectory,labels=capture(a['body'],delta,candidate)
    support,seen=periodic_prefix(9390);vertices=[p.v for p in support.polytopes]
    ball=interval_ball(vertices,93.9,93.9+trajectory[-1,3]+.2)
    minimum=float(geometry.pose_values(field(known,ball),trajectory[:,:3]).min())
    end=trajectory[-1,:3];target=np.asarray(a['segment']['poses'][0]);position=float(np.linalg.norm(end[:2]-target[:2]));angle=abs(math.atan2(math.sin(end[2]-target[2]),math.cos(end[2]-target[2])))
    center=[end[0]+.3*math.cos(end[2]),end[1]+.3*math.sin(end[2]),end[2],0.,0.]
    geometric,p=validate(a['segment'],center,known,ball)
    capture_proof=dict(nominal_capture_passed=position<=.12 and angle<=.20 and minimum>=.22,
        position_error_m=position,heading_error_rad=angle,full_timed_enclosure_minimum_m=minimum,nominal_duration_s=float(trajectory[-1,3]),
        complete_next_segment_geometric_passed=geometric,complete_next_segment_geometry=p,initial_actual_center_steering_rad=delta,
        source_observations=seen,periodic_source_tick=support.source_tick,causal_vertices=vertices,interval_ball=[*ball[0].tolist(),ball[1]],
        trajectory=trajectory.tolist(),gears=labels,actual_response_qualified=False,models=0,physical_native=0)
    dump(O/'CAPTURE_NOMINAL_PROBE.json',capture_proof)
    # Source32210 is the final observed prefix in this original run. Prove its
    # vertices exactly match the recorded online snapshot, never use later data.
    b=states[32210];model=read(RAW/'CAUSAL_PREDICTION_MODEL.json')['periodic'];assert model['source_tick']<=32210
    assert read(RAW/'CAUSAL_PREDICTION_MODEL.json')['last_observed_time']<=322.1+1e-8
    vertices=[np.asarray(v) for v in model['vertices']];poses=np.asarray(b['segment']['poses']);length=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(poses[:,:2],axis=0),axis=1))]
    # This is a necessary diagnostic with explicit conservative cruise time and
    # hold. A pose sequence is not yet a qualified actual steering/brake profile.
    tests=[]
    for wait in [0.,5.,10.,15.,20.,25.,30.,35.,40.]:
        minimum=1e6
        times=length/.1+3.;total=float(times[-1]+2.)
        hold=np.array([b['body'][0]-.3*math.cos(b['body'][2]),b['body'][1]-.3*math.sin(b['body'][2]),b['body'][2]])
        if wait>0:minimum=min(minimum,float(geometry.pose_values(field(known,interval_ball(vertices,322.1,322.1+wait)),[hold])[0]))
        for pose,t in zip(poses,times):
            ball=interval_ball(vertices,322.1+wait+max(0.,t-.2),322.1+wait+t+.2)
            minimum=min(minimum,float(geometry.pose_values(field(known,ball),[pose])[0]))
        ball=interval_ball(vertices,322.1+wait+times[-1],322.1+wait+total+.2)
        minimum=min(minimum,float(geometry.pose_values(field(known,ball),[poses[-1]])[0]))
        tests.append(dict(wait_s=wait,minimum_clearance_m=minimum,necessary_sparse_check_passed=minimum>=.22,total_s=wait+total))
    dump(O/'TIME_INTERVAL_DIAGNOSTIC.json',dict(tests=tests,complete_motion_witness=False,source_native=32210,no_later_observations_used=True,models=0,physical_native=0))
    result=dict(capture_nominal_passed=capture_proof['nominal_capture_passed'],capture_position_m=position,capture_heading_rad=angle,capture_minimum_m=capture_proof['full_timed_enclosure_minimum_m'],
        timed_sparse_necessary_passes=sum(t['necessary_sparse_check_passed'] for t in tests),full_timed_handoff_qualified=False,actual_response_qualified=False,
        models=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-begin)
    dump(O/'PROBE_SUMMARY.json',result);print(json.dumps(result));signal.alarm(0)
if __name__=='__main__':main()
