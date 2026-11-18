"""Fixed real measurement -> single controller -> native plant, no state write."""
from gap_tools import *
import math
sys.path.insert(0,str(R/'experiments/v1157_response_execution'))
old=load('v1177_old_recording_primitives',R/'experiments/v1157_response_execution/response_execution.py')
Adapter=old.Adapter
def measured(vehicle):
    return dict(old.measured(vehicle),steering_load_episode=bool(getattr(vehicle,'_gap_loaded',False)))
def stopped(packet):return old.stopped(packet)
def proof(setup,packet,ss,uu):
    geom=old.ref._old.Geometry(setup['known'],None);low=float(geom.clearances(ss[:,:3])[0].min());lim=np.array(setup['limits']);rate=np.array(setup['slew_per_second'])*.01
    checks=dict(complete=ss.shape==(2201,8)and uu.shape==(2200,4),initial=float(abs(ss[0]-origin(packet)['state']).max())<=1e-8,finite=bool(np.isfinite(ss).all()and np.isfinite(uu).all()),raw=low>=q.REQUIRED,body=bool((abs(ss[:,3:6])<=[.13,.03,.16]).all()),ctrl=bool((uu>=lim[:,0]-1e-10).all()and(uu<=lim[:,1]+1e-10).all()),slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],uu]),axis=0))<=rate+1e-10).all()),rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015))
    return dict(passed=all(checks.values()),checks=checks,minimum_raw=low,packet=packet,analytic_native=2200,loaded_model='V1159')
class StopCertifier:
    def __init__(self,setup):self.setup=setup;self.engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);self.rows=[]
    def __call__(self,packet):
        ss,uu,_=self.engine.simulate(origin(packet),[(0.,0.,2200,0)]);p=proof(self.setup,packet,ss,uu);self.rows.append(p);assert p['passed'],'MEASURED_COMPLETE_STOP_REFUSED';return p
class FunctionalRefusal(Exception):pass
def run_component(vehicle,plan,certify,permit,checkpoint):
    assert not getattr(vehicle,'_gap_executing',False),'SECOND_CONTROL_OWNER'
    assert vehicle.count==0 and len(plan['states'])==len(plan['requests'])+1
    vehicle._gap_executing=True;vehicle._gap_loaded=False;vehicle._gap_journal=[];maximum=np.zeros(3);feature=np.zeros(2)
    def step(v,w,phase,expected=None,drive=False):
        nonlocal maximum,feature
        before=measured(vehicle);old.require_body(before)
        if not permit(drive):raise FunctionalRefusal('DRIVE_TIME_RESERVE')if drive else AssertionError('STOP_TIME_RESERVE')
        if vehicle.count%8==0:certify(before)
        row=dict(before_native=vehicle.count,phase=phase,request=[float(v),float(w),False],packet=before,last_ctrl=vehicle.adapter.last.tolist(),integral=float(vehicle.adapter.integral),applied=False);vehicle._gap_journal.append(row)
        vehicle.adapter.parked_target=None;prior=vehicle.count;vehicle.step(float(v),float(w),False);assert vehicle.count==prior+1,'NATIVE_STEP_COUNT';row['applied']=True
        if v>=.005:vehicle._gap_loaded=True
        after=measured(vehicle);old.require_body(after);state=np.array(origin(after)['state']);feature=np.maximum(feature,abs(state[[7,4]]))
        if vehicle.count%5==0:vehicle.scan()
        if expected is not None:
            error=old.response(after,expected);maximum=np.maximum(maximum,error);row['response_error']=error
            if not(error<=[.04,.035,.015]).all():raise FunctionalRefusal('ACTUAL_MODEL_RESPONSE_ERROR')
        if vehicle.count%100==0:checkpoint(dict(native=vehicle.count,phase=phase,response_max=maximum,observed_rate_lateral=feature))
    failure=None
    try:
        vehicle.scan();old.require_body(measured(vehicle));previous_drive=False
        for i,(v,w,stale)in enumerate(plan['requests']):
            drive=bool(v)
            if drive!=previous_drive:certify(measured(vehicle))
            step(v,w,'fixed_input',plan['states'][i+1],drive);previous_drive=drive
        assert stopped(measured(vehicle)),'FULL_COMPONENT_NOT_STOPPED'
        result=dict(passed=True,normal_complete=True,component_complete=True)
    except FunctionalRefusal as exc:
        failure=dict(reason=str(exc),native=vehicle.count,packet=measured(vehicle));checkpoint(dict(stage='functional_refusal',failure=failure));certify(measured(vehicle))
        for _ in range(2200):step(0.,0.,'functional_stop',None,False)
        assert stopped(measured(vehicle)),'FUNCTIONAL_STOP_NOT_REACHED'
        result=dict(passed=False,normal_complete=False,component_complete=False,functional_failure=failure)
    finally:vehicle._gap_executing=False
    result.update(actual_native=vehicle.count,capture_native=0,maximum_response_error=maximum,observed_rate_lateral=feature,original_goal_passed=False,scope='fixed static response stimulus only')
    return result
