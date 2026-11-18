"""Production saved audit over measured fixture, never new physical success."""
from chain_tools import *
import tempfile,copy
def main():
    assert read(O/'QUALIFICATION.json')['passed'];review=load('v1180_production_review_fixture',C/'audit.py');parent=R/'runs/v858_nav2_verified/v1179/main';sw=O/'software_rehearsal'
    with tempfile.TemporaryDirectory(dir=O,prefix='saved_audit_fixture_')as d:
        out=Path(d);(out/'physics').mkdir()
        for name in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','scene_model.mjb','SETUP.json','INITIAL_STATE.npz']:(out/'physics'/name).hardlink_to(parent/'physics'/name)
        for name in ['CANONICAL_INITIAL_PACKET.json']:(out/name).hardlink_to(parent/name)
        for name in ['DIRECT_SEGMENTS.json','OBSERVATION_ENTRY.json','OBSERVER_CERTIFICATES.json','REFRESH_SEAM.json','REFRESH_INPUT.json','LIVE_REFRESH_PROOFS.json','RECOVERY_INPUT.json','LIVE_JOINT_TABLE.npz','LIVE_RECOVERY_REFERENCE.npz','LIVE_RECOVERY_REFERENCE_PROOF.json','RECOVERY_POLICY_RESULT.json','RECOVERY_POLICY_JOURNAL.json','RECOVERY_SHADOW.npz']:(out/name).hardlink_to(sw/name)
        with np.load(parent/'physics/NATIVE_TRACE.npz')as z:states=review.projection(z['qpos'],z['qvel'],read(parent/'physics/SETUP.json'))
        p0=read(parent/'CANONICAL_INITIAL_PACKET.json');states=np.vstack([q.initial(p0)['state'],states]);cmd=np.array(read(parent/'physics/BODY_COMMANDS.json'));old1=read(R/'runs/v858_nav2_verified/v1144/observation_main/MODE_JOURNAL.json');old2=read(R/'runs/v858_nav2_verified/v1148/component_main/MODE_JOURNAL.json');owner=q.model.Predictor(read(parent/'physics/SETUP.json'),dict(q.initial(p0),steering_load_episode=False)).adapter;journal=[]
        for i,c in enumerate(cmd):
            row=None if i<20160 or i>=34723 else old1[i-20160]if i<32515 else old2[i-32515];target=row['target']if row and row['mode']else None;journal.append(dict(before_native=i,phase='synthetic_saved_audit_fixture',parked_target=target,request=c[[1,2,5]].tolist(),last_ctrl=owner.last.copy(),integral=owner.integral,applied=True));owner.parked_target=target;owner.compute(*c[[1,2,3,4]],bool(c[5]))
        dump(out/'APPLIED_JOURNAL.json',journal);r=read(parent/'RESULT.json');r.update(historical_reconstruction_native=0,historical_controls_used=0,new_actual_native=len(cmd),total_actual_model_native=len(cmd),first_causal_discovery_native=read(O/'QUALIFICATION.json')['first_causal_discovery_native'],synthetic_measured_fixture_not_new_physical_success=True);dump(out/'RESULT.json',r)
        task=dict(read(C/'TASK_main.json'),output=str(out));proof=review.audit(task);negative=[]
        j=copy.deepcopy(journal);j[0]['request'][0]=.2;dump(out/'APPLIED_JOURNAL.json',j)
        try:review.audit(task)
        except AssertionError:negative.append('applied_request_tamper')
        else:raise AssertionError('AUDIT_ACCEPTED_REQUEST_TAMPER')
        j=copy.deepcopy(journal);j[0]['integral']=.1;dump(out/'APPLIED_JOURNAL.json',j)
        try:review.audit(task)
        except AssertionError:negative.append('control_memory_tamper')
        else:raise AssertionError('AUDIT_ACCEPTED_MEMORY_TAMPER')
        dump(O/'AUDIT_QUALIFICATION.json',dict(passed=True,production_saved_audit=proof,negative_cases=negative,models=0,new_mujoco_native=0,fixture_uses_old_measured_data_not_new_physical_result=True,analytical_cpp_native=proof['analytical_cpp_native'],additional_negative_partial_cpp_native=0));print('V1180_PRODUCTION_SAVED_AUDIT_QUALIFIED')
if __name__=='__main__':main()
