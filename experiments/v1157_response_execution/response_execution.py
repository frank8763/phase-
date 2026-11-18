"""Uniquely named single-owner profile and causal capture execution."""
from response_tools import R,load
import math
import sys
import time
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import Adapter,REQUIRED,ref
from source import Engine,initial
from runtime import Predictor
capture=load('v1157_frozen_capture',R/'experiments/v1152_terminal_capture_qualification/capture.py')


class FunctionalRefusal(Exception):pass


def measured(vehicle):
    b=list(vehicle.body());e=vehicle.steering_sample();now=time.monotonic()
    lat=float(-vehicle.d.qvel[0]*math.sin(b[2])+vehicle.d.qvel[1]*math.cos(b[2]))
    return dict(body=b,body_lateral=lat,native_tick=vehicle.count,sim_time=float(vehicle.d.time),
        body_measured_at=now,sent_at=now,dynamic_discovered=False,
        steering=dict(position=e[:2].tolist(),velocity=e[2:].tolist(),native_tick=vehicle.count,measured_at=now),
        controller_memory=dict(last_ctrl=vehicle.adapter.last.tolist(),integral=float(vehicle.adapter.integral)),
        coupled_episode=False,steering_motion_active=False)


def stopped(packet):
    return bool(abs(np.asarray(packet['body'][3:])).max()<=.003 and
                abs(np.asarray(packet['steering']['velocity'])).max()<=.015)


def capture_target(packet):
    assert stopped(packet), 'CAPTURE_REQUIRES_COMPLETE_ACTUAL_STOP'
    b=packet['body'];return np.array([b[0]+.04*math.cos(b[2]),b[1]+.04*math.sin(b[2]),b[2]])


def response(actual,expected):
    a=np.array(initial(actual)['state']);delta=a-expected
    return np.array([np.linalg.norm(delta[:2]),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(delta[6])])


def require_body(packet):
    b=packet['body'];lat=packet['body_lateral']
    assert np.isfinite([*b,lat,*packet['steering']['position'],*packet['steering']['velocity']]).all(),'NONFINITE_ACTUAL_PACKET'
    assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(lat)<=.03,'ACTUAL_BODY_CAP'
    assert abs(packet['sim_time']-.01*packet['native_tick'])<=1e-8,'ACTUAL_CLOCK'


def stop_proof(setup,packet,ss,uu,geometry):
    assert ss.shape==(2201,8) and uu.shape==(2200,4),'COMPLETE_STOP_SHAPES'
    assert np.isfinite(ss).all() and np.isfinite(uu).all(),'NONFINITE_STOP'
    assert np.max(abs(ss[0]-initial(packet)['state']))<=1e-8,'STOP_INITIAL_BINDING'
    low=float(geometry.clearances(ss[:,:3])[0].min());limits=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    checks=dict(raw=low>=REQUIRED,body=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),
        legal=bool((uu>=limits[:,0]-1e-10).all()and(uu<=limits[:,1]+1e-10).all()),
        slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),
        complete=len(uu)==2200,rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015))
    return dict(passed=all(checks.values()),checks=checks,minimum_raw_m=low,packet=packet,
                analytic_native=2200,source='original full2200 static stop model, not a robust tube')


class StopCertifier:
    def __init__(self,setup):
        self.setup=setup;self.engine=Engine(setup);self.rows=[]
        self.geometry=ref._old.Geometry(setup['known'],None)

    def __call__(self,packet):
        ss,uu=self.engine.simulate(initial(packet),[(0.,0.,2200,0)])
        proof=stop_proof(self.setup,packet,ss,uu,self.geometry)
        self.rows.append(proof)
        assert proof['passed'],'MEASURED_COMPLETE_STOP_UNQUALIFIED'
        return proof


def run_component(vehicle,plan,certify,permit,checkpoint,predictor_factory=Predictor):
    """Production control flow. Tests may substitute data-only vehicle/dependencies."""
    assert not getattr(vehicle,'_v1157_executing',False),'SECOND_CONTROL_OWNER'
    vehicle._v1157_executing=True
    journal=[];maximum=np.zeros(3);capture_origin=None;target=None;capture_native=0
    capture_prediction_native=0;predicting=False
    def step(v,w,phase,expected=None,allow_drive=True):
        nonlocal maximum
        before=measured(vehicle);require_body(before)
        if not permit(allow_drive):
            if allow_drive:raise FunctionalRefusal('COMPONENT_DRIVE_TIME_RESERVE')
            raise AssertionError('COMPONENT_STOP_TIME_RESERVE')
        if vehicle.count%8==0:certify(before)
        row=dict(before_native=vehicle.count,phase=phase,request=[float(v),float(w),False],
                 last_ctrl=before['controller_memory']['last_ctrl'],integral=before['controller_memory']['integral'],
                 packet=before,applied=False)
        journal.append(row)
        vehicle.adapter.parked_target=None
        old=vehicle.count;vehicle.step(float(v),float(w),False)
        assert vehicle.count==old+1,'NATIVE_COUNT_CONTRACT'
        row['applied']=True
        after=measured(vehicle);require_body(after)
        if expected is not None:
            error=response(after,expected);maximum=np.maximum(maximum,error);row['response_error']=error.tolist()
            if not (error<=[.04,.035,.015]).all():raise FunctionalRefusal('ACTUAL_MODEL_RESPONSE_ERROR')
        if vehicle.count%5==0:vehicle.scan()
        if vehicle.count%100==0:checkpoint(dict(native=vehicle.count,phase=phase,maximum_response_error=maximum))

    def stop_tail(phase):
        certify(measured(vehicle))
        for _ in range(2200):step(0.,0.,phase,allow_drive=False)
        assert stopped(measured(vehicle)), 'COMPLETE_ACTUAL_STOP_NOT_REACHED'

    failure=None
    try:
        require_body(measured(vehicle))
        vehicle.scan()
        for i in range(6400):
            v,w,_=plan['requests'][i]
            phase='initial_hold' if i<2200 else 'changing_drive' if i<4200 else 'drive_stop'
            step(v,w,phase,plan['states'][i+1],allow_drive=bool(v))
        capture_origin=measured(vehicle);target=capture_target(capture_origin)
        checkpoint(dict(stage='capture_origin',packet=capture_origin,target=target))
        certify(capture_origin)
        p=predictor_factory(vehicle._v1157_setup,initial(capture_origin))
        for _ in range(600):
            current=measured(vehicle);state=np.asarray(initial(current)['state'])
            v,w,status=capture.request(state,target)
            if status=='CAPTURED':break
            if status!='CAPTURING':raise FunctionalRefusal(status)
            predicting=True;expected,_=p.step(v,w,False);predicting=False;capture_prediction_native+=1
            step(v,w,'capture',expected);capture_native+=1
        else:raise FunctionalRefusal('CAPTURE_WORK_CAP')
        certify(measured(vehicle))
        for _ in range(2200):
            predicting=True;expected,_=p.step(0.,0.,False);predicting=False;capture_prediction_native+=1
            step(0.,0.,'capture_stop',expected,allow_drive=False)
        final=measured(vehicle)
        distance=float(np.linalg.norm(np.array(final['body'][:2])-target[:2]));yaw=abs(math.atan2(math.sin(final['body'][2]-target[2]),math.cos(final['body'][2]-target[2])))
        if not stopped(final)or distance>.025 or yaw>.1:raise FunctionalRefusal('CAPTURE_TERMINAL_REFUSED')
        result=dict(passed=True,normal_complete=True,capture_native=capture_native,capture_target=target,
                    capture_origin=capture_origin,terminal_position_error_m=distance,terminal_yaw_error_rad=yaw)
    except FunctionalRefusal as e:
        failure=dict(reason=str(e),native=vehicle.count,packet=measured(vehicle))
        checkpoint(dict(stage='functional_refusal',failure=failure))
        stop_tail('functional_stop')
        result=dict(passed=False,normal_complete=False,functional_failure=failure,
                    capture_native=capture_native,capture_target=target,capture_origin=capture_origin)
    finally:
        vehicle._v1157_executing=False
        vehicle._v1157_journal=journal
        vehicle._v1157_capture_prediction_native=capture_prediction_native
        vehicle._v1157_prediction_inflight=predicting
    result.update(maximum_response_error=maximum,actual_native=vehicle.count,
                  capture_prediction_native=capture_prediction_native,maximum_actual_native_cap=11400,
                  original_goal_passed=False,scope='one static response/capture component')
    return result
