"""Production flow on saved-array substitutes. No plant or prediction steps."""
from response_tools import *
import ast
import copy
import gzip
import importlib.abc
import tempfile
import types
import fcntl
import math
import numpy as np


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','rclpy','vehicle'}:
            raise AssertionError('ZERO_MODEL_QUALIFICATION '+name)


sys.meta_path.insert(0,NoModels())
import response_execution as execution
actual_audit=load('v1157_production_saved_audit',C/'audit.py')


def run():
    assert not (O/'QUALIFICATION.json').exists(),'ONE_ENTRY_QUALIFICATION_ONLY'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')==GUARD_SHA
    with np.load(R/'runs/v1156_response_input_preparation/PLAN.npz') as z:plan={k:z[k].copy()for k in z.files}
    fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json')
    setup=fixture['setup'];ss=plan['states'];rr=plan['requests'];uu=plan['controls'];mm=plan['memory'];n=len(uu)
    class Vehicle:
        def __init__(self):
            self.count=0;self._v1157_setup=setup
            self.adapter=execution.Predictor(setup,execution.initial(fixture['packet'])).adapter
            self.commands=[];self.sensors=[];self.d=types.SimpleNamespace(qvel=np.zeros(19),time=0.)
            self.scan();self.scan() # original factory's true-t0 sensor binding pair
        def body(self):
            s=ss[self.count];return [*s[:4],s[5]]
        def steering_sample(self):
            s=ss[self.count];k=math.tan(s[6])/.6;h=.27
            angles=np.array([math.atan(.6*k/(1-h*k)),math.atan(.6*k/(1+h*k))])
            derivative=(1+math.tan(s[6])**2)/np.array([(1-h*k)**2+(.6*k)**2,(1+h*k)**2+(.6*k)**2])
            return np.r_[angles,derivative*s[7]]
        def scan(self):
            b=self.body();packet=dict(native_tick=self.count,time=self.count*.01,xy=b[:2],yaw=b[2],ranges=[3.]*32)
            self.sensors.append(packet);return packet
        def step(self,v,w,stale):
            i=self.count;assert i<n
            assert np.max(abs(np.array([v,w,float(stale)])-rr[i]))<=1e-12,'SUBSTITUTE_APPLIED_REQUEST'
            s=ss[i];command=self.adapter.compute(v,w,s[3],s[5],stale)
            assert np.max(abs(command-uu[i]))<=1e-10,'SUBSTITUTE_CONTROL'
            self.commands.append([0.,v,w,s[3],s[5],stale]);self.count+=1;after=ss[self.count]
            self.d.time=self.count*.01
            self.d.qvel[0]=after[3]*math.cos(after[2])-after[4]*math.sin(after[2])
            self.d.qvel[1]=after[3]*math.sin(after[2])+after[4]*math.cos(after[2]);self.d.qvel[5]=after[5]
    class SavedPredictor:
        def __init__(self,setup,origin):
            self.i=6400
            assert np.max(abs(np.array(origin['state'])-ss[6400]))<=1e-8
        def step(self,v,w,stale):
            i=self.i;assert np.max(abs(np.array([v,w,float(stale)])-rr[i]))<=1e-12
            self.i+=1;return ss[self.i].copy(),uu[i].copy()
    vehicle=Vehicle();certificates=[];events=[]
    def synthetic_certificate(packet):
        proof=dict(passed=True,checks=dict(synthetic_interface_only=True),minimum_raw_m=.35,
            packet=packet,analytic_native=2200,synthetic=True)
        certificates.append(copy.deepcopy(proof));return proof
    result=execution.run_component(vehicle,plan,synthetic_certificate,lambda *_:True,events.append,SavedPredictor)
    assert result['passed'] and vehicle.count==n and result['capture_native']==261
    assert np.max(abs(np.r_[vehicle.adapter.last,vehicle.adapter.integral]-mm[-1]))<=1e-10
    capture_event=next(e for e in events if e.get('stage')=='capture_origin')
    positives=1;rejected=[]
    class FunctionalStopVehicle(Vehicle):
        def body(self):
            b=fixture['packet']['body'].copy()
            if self.count:b[0]+=.05
            return b
        def steering_sample(self):return np.zeros(4)
        def step(self,v,w,stale):
            assert v==w==0. and stale is False
            self.adapter.compute(v,w,0.,0.,False)
            self.count+=1;self.d.time=self.count*.01;self.d.qvel[:]=0.
    fail_vehicle=FunctionalStopVehicle()
    functional=execution.run_component(fail_vehicle,plan,lambda p:dict(passed=True,synthetic=True),
        lambda *_:True,lambda _:None,SavedPredictor)
    assert not functional['passed'] and fail_vehicle.count==2201
    assert functional['functional_failure']['reason']=='ACTUAL_MODEL_RESPONSE_ERROR'
    assert all(row['phase']=='functional_stop'and row['request']==[0.,0.,False]
               for row in fail_vehicle._v1157_journal[-2200:])
    positives+=1
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError,IndexError):rejected.append(name)
        else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
    for name,change,permit,cert in [
        ('expired',lambda v:None,lambda *_:False,synthetic_certificate),
        ('second_owner',lambda v:setattr(v,'_v1157_executing',True),lambda *_:True,synthetic_certificate),
        ('missing_certificate',lambda v:None,lambda *_:True,lambda p:(_ for _ in ()).throw(AssertionError('missing'))),
    ]:
        v=Vehicle();change(v)
        reject(name,lambda v=v,permit=permit,cert=cert:execution.run_component(v,plan,cert,permit,lambda _:None,SavedPredictor))
        assert v.count==0
    wrong=copy.deepcopy(fixture['packet']);wrong['body'][3]=.14
    reject('initial_body_cap',lambda:execution.require_body(dict(wrong,body_lateral=0.)))
    moving=copy.deepcopy(fixture['packet']);moving['body'][3]=.01
    reject('capture_requires_stop',lambda:execution.capture_target(moving))
    packet=copy.deepcopy(vehicle._v1157_journal[n-2200]['packet'])
    # Tail arrays are immutable saved evidence; production stop geometry gate
    # is tested without propagating the state again.
    geom=execution.ref._old.Geometry(setup['known'],None)
    stop_ss=ss[-2201:].copy();stop_uu=uu[-2200:].copy()
    proof=execution.stop_proof(setup,packet,stop_ss,stop_uu,geom);assert proof['passed'];positives+=1
    reject('truncated_complete_stop',lambda:execution.stop_proof(setup,packet,stop_ss[:-1],stop_uu,geom))
    bad=stop_ss.copy();bad[0,0]+=.001
    reject('stop_initial_binding',lambda:execution.stop_proof(setup,packet,bad,stop_uu,geom))
    bad=stop_ss.copy();bad[10,3]=.14
    assert not execution.stop_proof(setup,packet,bad,stop_uu,geom)['passed'];rejected.append('stop_body_cap')
    O.mkdir(exist_ok=True);(O/'qualification_fixtures').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=O/'qualification_fixtures',prefix='saved_array_only_') as folder:
        out=Path(folder);(out/'physics').mkdir()
        actual_after=ss[1:];qpos=np.zeros((n,20));qvel=np.zeros((n,19));ctrl=np.zeros((n,11))
        qpos[:,:2]=actual_after[:,:2];qpos[:,2]=.2;qpos[:,3]=np.cos(actual_after[:,2]/2);qpos[:,6]=np.sin(actual_after[:,2]/2)
        k=np.tan(actual_after[:,6])/.6;front=np.c_[np.arctan(.6*k/(1-.27*k)),np.arctan(.6*k/(1+.27*k))]
        derivative=(1+np.tan(actual_after[:,6])**2)[:,None]/np.c_[(1-.27*k)**2+(.6*k)**2,(1+.27*k)**2+(.6*k)**2]
        qpos[:,setup['steering_qpos_addresses']]=front;qvel[:,setup['steering_qvel_addresses']]=derivative*actual_after[:,7,None]
        qvel[:,0]=actual_after[:,3]*np.cos(actual_after[:,2])-actual_after[:,4]*np.sin(actual_after[:,2])
        qvel[:,1]=actual_after[:,3]*np.sin(actual_after[:,2])+actual_after[:,4]*np.cos(actual_after[:,2]);qvel[:,5]=actual_after[:,5]
        ctrl[:,setup['actuator_ids']]=uu
        trace=dict(time=np.arange(1,n+1)*.01,qpos=qpos,qvel=qvel,ctrl=ctrl,
            clearance=np.full(n,.35),self_margin=np.full(n,.01),mocap_pos=np.empty((n,0,3)),mocap_quat=np.empty((n,0,4)))
        synthetic_result=dict(result,synthetic=True,models=1,new_actual_native=n,own_replay_native=n,
            fully_recorded_actual_native=n,error=None,physical=dict(bad_contacts=0,root_guard_native_count=n,
            fully_recorded_native=n,first_actor_detection=None),replay=dict(passed=True,replay_native=n,
            maximum_qpos_qvel_ctrl_mocap_error=0.,contact_mismatched_ticks=0))
        for file,value in [('RESULT.json',synthetic_result),('physics/SETUP.json',setup),('REQUEST_JOURNAL.json',vehicle._v1157_journal),
                           ('physics/BODY_COMMANDS.json',vehicle.commands),('ACTUAL_INITIAL_PACKET.json',fixture['packet']),
                           ('ACTUAL_CAPTURE_ORIGIN.json',capture_event),('MEASURED_STOP_CERTIFICATES.json',certificates)]:dump(out/file,value)
        np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
        for file,value in [('CONTACTS.json.gz',[[]for _ in range(n+1)]),('SENSORS.json.gz',vehicle.sensors)]:
            with gzip.open(out/'physics'/file,'wt')as f:json.dump(value,f)
        task=dict(output=str(out));proof=actual_audit.audit(task,save=False,synthetic=True,predictor_factory=SavedPredictor)
        assert proof['passed'];positives+=1
        mutations=[
            ('audit_changed_capture_target','ACTUAL_CAPTURE_ORIGIN.json',lambda d:d['target'].__setitem__(0,d['target'][0]+.001)),
            ('audit_wrong_request','physics/BODY_COMMANDS.json',lambda d:d[3000].__setitem__(1,.08)),
            ('audit_wrong_memory','REQUEST_JOURNAL.json',lambda d:d[3000].__setitem__('integral',d[3000]['integral']+.001)),
            ('audit_truncated_tail','RESULT.json',lambda d:d.__setitem__('capture_native',260)),
            ('audit_incomplete_stop_proof','MEASURED_STOP_CERTIFICATES.json',lambda d:d[0].__setitem__('analytic_native',2199)),
        ]
        for name,file,mutate in mutations:
            path=out/file;old=path.read_bytes();value=json.loads(old);mutate(value);dump(path,value)
            reject(name,lambda:actual_audit.audit(task,save=False,synthetic=True,predictor_factory=SavedPredictor));path.write_bytes(old)
        trace['ctrl'][3000,setup['actuator_ids'][2]]+=.001
        np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
        reject('audit_wrong_applied_control',lambda:actual_audit.audit(task,save=False,synthetic=True,predictor_factory=SavedPredictor))
        trace['ctrl'][3000,setup['actuator_ids'][2]]-=.001
        np.savez_compressed(out/'physics/NATIVE_TRACE.npz',**trace)
        assert actual_audit.audit(task,save=False,synthetic=True,predictor_factory=SavedPredictor)['passed'];positives+=1
    for file in C.glob('*.py'):ast.parse(file.read_text())
    # The production worker must reject before even entering its factory branch.
    worker=load('v1157_production_worker',C/'worker.py')
    dump(O/'APPROVAL.json',dict(models_authorized=False,scope='preparation only'))
    old_argv=sys.argv[:];sys.argv=['worker.py',str(C/'TASK_main.json')]
    try:reject('worker_no_model_authority',worker.main)
    finally:sys.argv=old_argv
    proof=dict(passed=True,positive_cases=positives,rejected_cases=rejected,
        production_executor_saved_array_calls=n,production_control_memory_match=True,
        production_saved_audit_synthetic_positive=True,synthetic_stop_verifier_not_a_safety_proof=True,
        no_physical_factory_or_model_imported=True,new_analytical_state_propagation=0,
        models=0,physical_native=0,training_updates=0,actual_response_verified=False,
        physical_window_opened=False,guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA)
    dump(O/'QUALIFICATION.json',proof);print(encode(proof))


if __name__=='__main__':run()
