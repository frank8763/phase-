"""Actual constructor, switch, dispatch recording and audit on metadata arrays.

Counters below are software call counters, never model integrations.
"""
import copy
import gzip
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
from control_fixture import R,O,NoModel

sys.path.insert(0,str(R/'experiments/v855_renewal_worker'))
import actuator_commands
import actuation_binding as binding
import actuation_audit as audit

NAMES=['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']
MJ=S(mjtObj=S(mjOBJ_ACTUATOR=0),mj_name2id=lambda m,k,n:NAMES.index(n))


class ArrayPeer:
    def __init__(self,out,origin=6083):
        self.out=out;out.mkdir(parents=True,exist_ok=False);self.dt=.01;self.count=origin
        self.m=S(actuator_ctrllimited=np.ones(4,bool),actuator_ctrlrange=np.array([[-.52,.52],[-.52,.52],[-20.,20.],[-20.,20.]]))
        self.d=S(qpos=np.r_[np.zeros(3),1.,np.zeros(16)],qvel=np.r_[np.zeros(5),-.02,np.zeros(13)],
            ctrl=np.zeros(4),mocap_pos=np.zeros((1,3)),mocap_quat=np.array([[1.,0.,0.,0.]]),time=origin*.01,
            actuator_force=np.zeros(4),qfrc_actuator=np.zeros(19),qfrc_constraint=np.zeros(19))
        self.adapter=binding.control.base.Adapter(self.m,MJ,self.dt,encoders=lambda:(self.d.qpos[[7,9]],self.d.qvel[[6,8]]))
        self.rows=[np.zeros(4).copy()for _ in range(origin)]
        self.commands=[[0.,0.,0.,0.,0.,True]for _ in range(origin)]
        self.qrows=[self.d.qpos.copy()for _ in range(origin)];self.vrows=[self.d.qvel.copy()for _ in range(origin)]
        self.setup=dict(limits=self.m.actuator_ctrlrange.tolist(),slew_per_second=[1.25,1.25,8.75,8.75],
            actuator_ids=[0,1,2,3],steering_qpos_addresses=[7,9],steering_qvel_addresses=[6,8],adapter_revision='V958')
        (out/'SETUP.json').write_text(json.dumps(self.setup))
    def body(self):return audit.body(self.d.qpos,self.d.qvel)
    def steering_sample(self):return np.r_[self.d.qpos[[7,9]],self.d.qvel[[6,8]]]
    def step(self,v,w,stale=False):
        pre=self.body();u=self.adapter.compute(v,w,*pre[3:5],stale)
        self.d.ctrl[:]=u;self.count+=1;self.d.time=self.count*.01
        # No plant update; states are deliberately held metadata arrays.
        self.commands.append([0.,v,w,*pre[3:5],stale]);self.rows.append(u.copy())
        self.qrows.append(self.d.qpos.copy());self.vrows.append(self.d.qvel.copy())
    def finish(self):
        np.savez_compressed(self.out/'NATIVE_TRACE.npz',ctrl=self.rows,qpos=self.qrows,qvel=self.vrows)
        (self.out/'BODY_COMMANDS.json').write_text(json.dumps(self.commands))
        return dict(explicit_array_fixture=True,models=0,integrations=0)


def main():
    checks={};negatives=[];work=O/'binding_qualified';work.mkdir(exist_ok=False)
    dest=work/'binding_fixture';dest.mkdir(exist_ok=False)
    task=dict(origin_native_tick=6083,origin_sim_time=60.83,stage='component')
    peer=ArrayPeer(dest/'physics');before=peer.d.qpos.copy()
    proof=binding.bind_restored(peer,task,peer.out,MJ)
    checks['actual_constructor_original_command_map']=type(peer.adapter.commands)is actuator_commands.CommandMap
    checks['actual_selected_class_source']=Path(inspect.getsourcefile(peer.adapter.compute)).resolve()==binding.SOURCE
    checks['memory_switch_does_not_advance_state']=np.array_equal(before,peer.d.qpos)and peer.count==6083 and proof['integrations']==0
    for i in range(150):peer.step(.05,.015 if i<75 else-.015,False)
    for _ in range(200):peer.step(0.,0.,True)
    peer.finish();positive=audit.check(dest,task)
    checks['actual_dispatch_recording_and_independent_mixed_audit']=positive['passed']
    path=peer.out/'ALLOCATION.json.gz';original=path.read_bytes();records=json.loads(gzip.decompress(original))
    checks['diagnostic_force_arrays_and_encoder_records_written']=all(set(r['pre_native_forces'])=={'actuator_force','qfrc_actuator','qfrc_constraint'}and len(r['pre_native_steering'])==4 for r in records)
    mutations=[('proof_curvature',lambda d:d[10]['proof'].__setitem__('selected_curvature',.5)),
        ('false_common',lambda d:d[10]['proof'].__setitem__('selected_common',3.)),
        ('wrong_tick',lambda d:d[0].__setitem__('native_tick',6085)),
        ('wrong_actual_ctrl',lambda d:d[10]['actual_ctrl'].__setitem__(2,1.)),
        ('missing_row',lambda d:d.pop()),
        ('false_stale',lambda d:d[-1].__setitem__('stale',False)),
        ('false_pre_body',lambda d:d[10]['pre_native_body'].__setitem__(4,.1)),
        ('false_post_body',lambda d:d[10]['post_native_body'].__setitem__(3,.1)),
        ('false_encoder',lambda d:d[10]['pre_native_steering'].__setitem__(0,.1)),
        ('false_measured_feedback',lambda d:d[10]['proof']['measured'].__setitem__(1,.1))]
    for label,mutate in mutations:
        changed=copy.deepcopy(records);mutate(changed);path.write_bytes(gzip.compress(json.dumps(changed).encode()))
        try:audit.check(dest,task)
        except AssertionError:negatives.append(dict(case=label,rejected=True))
        else:negatives.append(dict(case=label,rejected=False))
    path.write_bytes(original)
    checks['ten_final_control_evidence_mutations_rejected']=all(x['rejected']for x in negatives)
    for name,field,value in [('advanced_origin','origin_native_tick',6084),('wrong_clock','origin_sim_time',60.84),('wrong_scope','stage','navigation')]:
        other=ArrayPeer(work/name);bad=dict(task);bad[field]=value
        try:binding.bind_restored(other,bad,other.out,MJ)
        except AssertionError:checks[name+'_denied_before_switch']=True
        else:checks[name+'_denied_before_switch']=False
    moving=ArrayPeer(work/'moving_origin');moving.d.qvel[0]=.04
    try:binding.bind_restored(moving,task,moving.out,MJ)
    except AssertionError:checks['moving_origin_denied_before_switch']=True
    else:checks['moving_origin_denied_before_switch']=False
    lateral=ArrayPeer(work/'lateral_origin');lateral.d.qvel[1]=.04
    try:binding.bind_restored(lateral,task,lateral.out,MJ)
    except AssertionError:checks['lateral_moving_origin_denied_before_switch']=True
    else:checks['lateral_moving_origin_denied_before_switch']=False
    # The chosen source can be imported and exercised only as a software object;
    # no physical factory/launcher is included in this source-only candidate.
    assert 'mujoco'not in sys.modules
    checks['metadata_proxy_not_model_initialization']=True
    sys.path.insert(0,str(Path(__file__).parent))
    import authority,native_worker,ros_worker,audit as complete_audit
    from transaction import TrackingGuard
    from independent_tracking import check as precise_tracking
    candidate=Path(__file__).resolve().parent
    checks['actual_native_engine_selected']=native_worker.engine.C.resolve()==candidate
    checks['actual_ros_engine_selected']=ros_worker.engine.C.resolve()==candidate
    checks['actual_precise_guard_selected']=Path(inspect.getsourcefile(TrackingGuard)).resolve()==candidate/'tracking.py'
    checks['actual_dense_audit_selected']=complete_audit.dense_tracking is precise_tracking
    checks['actual_actuation_audit_selected']=audit.source==binding.SOURCE
    try:native_worker.engine.run({}, {}, '')
    except PermissionError:checks['actual_engine_denies_before_model_import']=True
    else:checks['actual_engine_denies_before_model_import']=False
    result=dict(passed=all(checks.values()),checks=checks,negative_cases=negatives,mixed_audit=positive,
        models=0,integrations=0,explicit_metadata_array_fixture=True,canonical_model_audit_performed=False,
        factory_engine_module_binding_qualified=True,physical_tracking_qualified=False,physical_ready=False,models_authorized=False)
    (O/'BINDING_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));assert result['passed']


if __name__=='__main__':main()
