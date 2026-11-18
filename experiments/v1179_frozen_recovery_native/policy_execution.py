"""Frozen feedback native-evaluation policy, no formal-retention commit."""
from recovery_tools import *
def run_policy(v,reference,schedule,permit,checkpoint,predictor_factory=q.model.Predictor):
    assert v.count==HISTORY and not getattr(v,'_recovery_owner',False),'BAD_SOURCE_OR_SECOND_OWNER';v._recovery_owner=True;v.adapter.parked_target=None
    org=dict(q.initial(packet(v)),steering_load_episode=False);shadow=predictor_factory(v._recovery_setup,org);journal=[];maximum=np.zeros(3);posemax=np.zeros(2);target=reference['states'][-1,:3].copy();capture_n=0;shadowstates=[np.array(org['state'])];prediction_count=0;predicting=False
    def step(vr,wr,phase,reference_index):
        nonlocal maximum,posemax,prediction_count,predicting
        assert permit(),'NATIVE_QUALIFICATION_DEADLINE_RESERVE'
        before=packet(v);body_gate(before);state=np.array(q.initial(before)['state']);memory=before['controller_memory']
        row=dict(before_native=v.count,local_native=v.count-HISTORY,phase=phase,reference_index=reference_index,request=[float(vr),float(wr),False],packet=before,last_ctrl=memory['last_ctrl'],integral=memory['integral'],applied=False);journal.append(row)
        predicting=True;expected,_=shadow.step(float(vr),float(wr),False);predicting=False;prediction_count+=1;shadowstates.append(expected)
        v.adapter.parked_target=None;old=v.count;v.step(float(vr),float(wr),False);assert v.count==old+1;row['applied']=True
        after=packet(v);body_gate(after);actual=np.array(q.initial(after)['state']);diff=actual-expected;error=np.array([np.linalg.norm(diff[:2]),abs(math.atan2(math.sin(diff[2]),math.cos(diff[2]))),abs(diff[6])]);maximum=np.maximum(maximum,error);row['shadow_response_error']=error
        rp=reference['states'][reference_index];d=actual-rp;pose=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))]);posemax=np.maximum(posemax,pose);row['reference_pose_error']=pose
        if v.count%5==0:v.scan()
        assert(error<=[.04,.035,.015]).all(),'ACTUAL_SHADOW_MODEL_RESPONSE_REFUSED'
        assert(pose<=[.04,.035]).all(),'ACTUAL_TIME_REFERENCE_POSE_REFUSED'
        if (v.count-HISTORY)%100==0:checkpoint(dict(stage='actual_fixed_recovery',local_native=v.count-HISTORY,absolute_native=v.count,maximum_response_error=maximum,maximum_reference_pose_error=posemax))
    try:
        for i,(turn,speed)in enumerate(schedule):
            measured=np.array(q.initial(packet(v))['state']);vr,wr,_=q.tracking.request(measured,reference['states'][i],turn,speed);step(vr,wr,'reference',i+1)
        assert stopped(packet(v)),'FIRST_COMPLETE_STOP_NOT_REACHED'
        distance=float(np.linalg.norm(np.array(packet(v)['body'][:2])-target[:2]));status='NOT_REQUIRED'
        if distance>.025:
            for _ in range(600):
                vr,wr,status=q.capture.request(np.array(q.initial(packet(v))['state']),target)
                if status=='CAPTURED':break
                assert status=='CAPTURING','FORWARD_CAPTURE_REFUSED';step(vr,wr,'capture',5885);capture_n+=1
            else:raise AssertionError('CAPTURE_CAP')
        for _ in range(2200):step(0.,0.,'final_stop',5885)
        final=packet(v);dist=float(np.linalg.norm(np.array(final['body'][:2])-[4.,-2.]));target_dist=float(np.linalg.norm(np.array(final['body'][:2])-target[:2]));angle=abs(math.atan2(math.sin(final['body'][2]-target[2]),math.cos(final['body'][2]-target[2])))
        assert stopped(final)and target_dist<=.025 and angle<=.1,'ACTUAL_TERMINAL_REFUSED'
        assert dist+.08<=.45,'ORIGINAL_GOAL_REFUSED'
        return dict(passed=True,new_recovery_native=v.count-HISTORY,capture_native=capture_n,capture_status=status,goal_distance_m=dist,goal_upper_m=dist+.08,terminal_position_error=target_dist,terminal_heading_error=angle,maximum_model_response_error=maximum,maximum_reference_pose_error=posemax,final_stop_executed=True,formal_retained_commit=False,universal_error_support_verified=False,scope='one finite original saved-task recovery native qualification')
    finally:
        v._recovery_owner=False;v._recovery_journal=journal;v._recovery_shadow=np.array(shadowstates);v._recovery_python_native=prediction_count;v._recovery_python_inflight=predicting
