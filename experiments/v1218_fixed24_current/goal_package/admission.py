"""Finite feedback/continuous-shadow preview; no physical model or sensor claims."""
import copy,math,time
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'experiments/v1201_refuge_onward_connection'))
from .candidate_search import q,np,PreviewGeometry


def predictor_origin(p):
    return dict(state=p.state.copy(),last_ctrl=p.adapter.last.copy(),integral=float(p.adapter.integral),
        coupled_episode=bool(p.coupled_episode),steering_motion_active=bool(getattr(p,'steering_motion_active',False)),
        steering_load_episode=bool(p.steering_load_episode))


def check_arrays(x,table,origin,offset,states,controls,memory,requests,shadow,target):
    geometry=PreviewGeometry(q.Geometry(x,table),offset)
    local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=np.asarray(origin['last_ctrl']).tolist()
    actual_proof=q.proof(geometry,local,states,controls,requests,memory)
    shadow_proof=q.proof(geometry,local,shadow,controls,requests,memory)
    terminal=states[-1];distance=float(np.linalg.norm(terminal[:2]-target[:2]));yaw=abs(math.atan2(math.sin(terminal[2]-target[2]),math.cos(terminal[2]-target[2])))
    passed=bool(actual_proof['passed']and shadow_proof['passed']and distance<=.025 and yaw<=.1)
    return dict(passed=passed,feedback_proof=actual_proof,continuous_shadow_proof=shadow_proof,
        terminal_reference_distance_m=distance,terminal_reference_yaw_rad=yaw,
        nominal_preview_only=True,physical_eligible=False)


def preview(x,table,origin,shadow_origin,offset,candidate,deadline):
    """Original feedback law, capture and complete2200finalstop; carried shadow memory."""
    plant=q.model.Predictor(x['setup'],copy.deepcopy(origin))
    shadow=q.model.Predictor(x['setup'],copy.deepcopy(shadow_origin))
    ss=[plant.state.copy()];sh=[shadow.state.copy()];uu=[];mm=[np.r_[plant.adapter.last,plant.adapter.integral]];requests=[]
    maximum=np.zeros(3);posemax=np.zeros(2);reason=None
    def step(vr,wr,reference):
        nonlocal maximum,posemax
        assert time.monotonic()<deadline,'ADMISSION_DEADLINE'
        actual,u=plant.step(float(vr),float(wr),False);expected,_=shadow.step(float(vr),float(wr),False)
        ss.append(actual.copy());sh.append(expected.copy());uu.append(u.copy());mm.append(np.r_[plant.adapter.last,plant.adapter.integral]);requests.append([float(vr),float(wr),0.])
        d=actual-expected;e=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,e)
        d=actual-reference;pe=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))]);posemax=np.maximum(posemax,pe)
        assert(e<=[.04,.035,.015]).all(),'PREVIEW_RESPONSE_REFUSED'
        assert(pe<=[.04,.035]).all(),'PREVIEW_REFERENCE_REFUSED'
    try:
        ref=candidate['states'];i=0
        for target,speed,count,mode in candidate['rows']:
            assert not mode and speed in[0.,.12]
            for _ in range(int(count)):
                if speed==0.:vr=wr=0.
                else:vr,wr,_=q.tracking.request(plant.state,ref[i],float(target),float(speed))
                step(vr,wr,ref[i+1]);i+=1
        assert i==len(ref)-1
        target=ref[-1,:3];capture=0
        if np.linalg.norm(plant.state[:2]-target[:2])>.025:
            for _ in range(600):
                vr,wr,status=q.capture.request(plant.state,target)
                if status=='CAPTURED':break
                assert status=='CAPTURING','PREVIEW_CAPTURE_REFUSED'
                step(vr,wr,ref[-1]);capture+=1
            else:raise AssertionError('PREVIEW_CAPTURE_CAP')
        for _ in range(2200):step(0.,0.,ref[-1])
        arrays={k:np.asarray(v)for k,v in dict(states=ss,shadow=sh,controls=uu,memory=mm,requests=requests).items()}
        result=check_arrays(x,table,origin,offset,**arrays,target=target)
        result.update(capture_native=capture,maximum_response_error=maximum,maximum_reference_error=posemax)
    except AssertionError as exc:
        result=dict(passed=False,reason=str(exc),nominal_preview_only=True,physical_eligible=False)
        arrays={k:np.asarray(v)for k,v in dict(states=ss,shadow=sh,controls=uu,memory=mm,requests=requests).items()}
    result.update(native=len(uu),python_native=2*len(uu),offset=offset,origin=origin,shadow_origin=shadow_origin,
        shadow_memory_reset=False)
    return result,arrays
