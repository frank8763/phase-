"""Actual switch/audit seams on explicit metadata/array fixtures, zero models."""
import copy,gzip,hashlib,importlib.abc,inspect,json,sys
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v987_bounded_startup_components'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
# Bind candidate authority before legacy modules can alter search-path order.
import authority
import actuation_binding as binding
import actuation_audit
sys.path.insert(0,str(R/'experiments/v855_renewal_worker'))
import actuator_commands
NAMES=['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']
MJ=S(mjtObj=S(mjOBJ_ACTUATOR=0),mj_name2id=lambda m,k,n:NAMES.index(n))

class ArrayPeer:
    def __init__(self,out,origin=6083):
        self.out=out;out.mkdir(parents=True,exist_ok=False);self.count=origin;self.dt=.01
        self.m=S(actuator_ctrllimited=np.ones(4,bool),actuator_ctrlrange=np.array([[-.52,.52],[-.52,.52],[-20.,20.],[-20.,20.]]))
        self.d=S(qpos=np.r_[np.zeros(3),1.,np.zeros(16)],qvel=np.r_[np.zeros(5),-.05,np.zeros(13)],ctrl=np.zeros(4),
                 mocap_pos=np.zeros((1,3)),mocap_quat=np.array([[1.,0.,0.,0.]]),time=origin*.01)
        self.adapter=binding.control.base.Adapter(self.m,MJ,self.dt,encoders=lambda:(np.zeros(2),np.zeros(2)))
        self.rows=[np.zeros(4).copy()for _ in range(origin)]
        self.commands=[[0.,0.,0.,0.,0.,True]for _ in range(origin)]
        self.qrows=[self.d.qpos.copy()for _ in range(origin)];self.vrows=[self.d.qvel.copy()for _ in range(origin)]
        self.setup=dict(limits=self.m.actuator_ctrlrange.tolist(),slew_per_second=[1.25,1.25,8.75,8.75],actuator_ids=[0,1,2,3],adapter_revision='V958_KINEMATIC_MOVING_STEERING_HOLD_BRAKE')
        (out/'SETUP.json').write_text(json.dumps(self.setup))
    def step(self,v,w,stale=False):
        # Actual production map call and metadata recording, no plant update.
        u=self.adapter.compute(v,w,0.,-.05,stale);self.d.ctrl[:]=u;self.count+=1
        self.commands.append([0.,v,w,0.,-.05,stale]);self.rows.append(u.copy());self.qrows.append(self.d.qpos.copy());self.vrows.append(self.d.qvel.copy())
    def finish(self):
        np.savez_compressed(self.out/'NATIVE_TRACE.npz',ctrl=self.rows,qpos=self.qrows,qvel=self.vrows)
        (self.out/'BODY_COMMANDS.json').write_text(json.dumps(self.commands));return dict(explicit_array_fixture=True,models=0,integrations=0)

def main():
    attempt=int(sys.argv[1])if len(sys.argv)>1 else 1;fixture=O/f'binding_fixture_attempt{attempt}';fixture.mkdir(exist_ok=False);peer=ArrayPeer(fixture/'physics');task=dict(origin_native_tick=6083,origin_sim_time=60.83)
    before=peer.d.qpos.copy();proof=binding.bind_restored(peer,task,fixture/'physics',MJ)
    checks=dict(exact_old_compute_class=proof['old_control_source']=='experiments/v958_hold_steering_contract/vehicle_control.py',
        actual_selected_new_class=Path(inspect.getsourcefile(peer.adapter.compute)).resolve()==binding.SOURCE,
        constructor_reads_metadata_only=proof['integrations']==0 and peer.count==6083 and np.array_equal(before,peer.d.qpos),
        command_map_class_unchanged=type(peer.adapter.commands)is actuator_commands.CommandMap)
    for _ in range(12):peer.step(.05,.002,False)
    for _ in range(12):peer.step(0.,0.,True)
    peer.finish();positive=actuation_audit.check(fixture,task);checks['complete_mixed_old_new_map_reconstruction']=positive['passed']
    negatives=[]
    path=fixture/'physics/YAW_FEEDBACK.json.gz';original=path.read_bytes();data=json.loads(gzip.decompress(original))
    mutations=[('false_measured_yaw',lambda d:d[0]['proof']['measured'].__setitem__(1,.04)),
        ('wrong_tick',lambda d:d[0].__setitem__('native_tick',6085)),
        ('wrong_actual_motor',lambda d:d[0]['actual_ctrl'].__setitem__(2,1.)),
        ('missing_step',lambda d:d.pop()),
        ('false_stale',lambda d:d[-1].__setitem__('stale',False))]
    for label,mutate in mutations:
        changed=copy.deepcopy(data);mutate(changed);path.write_bytes(gzip.compress(json.dumps(changed).encode()))
        try:actuation_audit.check(fixture,task)
        except AssertionError:negatives.append(dict(case=label,rejected=True))
        else:negatives.append(dict(case=label,rejected=False))
    path.write_bytes(original)
    advanced=ArrayPeer(O/f'advanced_origin_fixture_attempt{attempt}')
    try:binding.bind_restored(advanced,dict(task,origin_native_tick=6084),advanced.out,MJ)
    except AssertionError:checks['advanced_origin_rejected_before_switch']=True
    else:checks['advanced_origin_rejected_before_switch']=False
    checks['negative_evidence_rejected']=all(n['rejected']for n in negatives)
    history={k:np.zeros((5,4))for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};requests=[[0.,0.,0.,0.,0.,True]for _ in range(5)]
    checks['independent_history_positive']=actuation_audit.compare_history(history,copy.deepcopy(history),requests,requests,5)['passed']
    for key in history:
        changed=copy.deepcopy(history);changed[key][2,1]=1e-6
        try:actuation_audit.compare_history(changed,history,requests,requests,5)
        except AssertionError:checks['independent_history_'+key+'_tamper_rejected']=True
        else:checks['independent_history_'+key+'_tamper_rejected']=False
    # Actual workers must resolve candidate modules while preserving original
    # online guard and independent precise limits, no physical module imported.
    sys.path.insert(0,str(C));import ros_worker;import native_worker;import audit
    from transaction import TrackingGuard
    from independent_tracking import check as independent_tracking
    checks['actual_ros_source_selected']=ros_worker.engine.C.resolve()==C
    checks['actual_native_source_selected']=native_worker.engine.C.resolve()==C
    checks['actual_dense_audit_selected']=audit.dense_tracking is independent_tracking
    checks['actual_actuation_audit_imports_declared_source']=actuation_audit.source==binding.SOURCE
    checks['precise_online_guard_source']=Path(inspect.getsourcefile(TrackingGuard)).resolve()==C/'tracking.py'
    report=dict(passed=all(checks.values()),checks=checks,negative_cases=negatives,positive_mixed_array_control_audit=positive,
        models=0,integrations=0,explicit_metadata_and_array_fixture=True,canonical_model_audit_performed=False,
        physical_tracking_qualified=False,physical_ready=False)
    (O/'BINDING_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
if __name__=='__main__':main()
