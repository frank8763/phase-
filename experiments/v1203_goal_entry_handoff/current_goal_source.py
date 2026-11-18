"""V1201 proposals with explicit carried origin/mode and absolute offset."""
import copy
import math
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1201_refuge_onward_connection'))
from preview_search import q,np,search,PreviewGeometry
from connection import CAP,compact,endpoint
from current_state_tools import validate_input


def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,onward_only=False):
    validate_input(x)
    preview=dict(origin=origin,native_offset=offset)
    direct=search(x,table,min(deadline,time.monotonic()+(8 if onward_only else 6)),checkpoint,preview=preview)
    work=direct['analytical_cpp_native']
    if direct['passed'] or onward_only or time.monotonic()>=deadline:
        direct.update(prefix_rows=None,analytical_cpp_native=work,method='direct')
        return direct
    fallback_end=min(deadline,time.monotonic()+25)
    g=PreviewGeometry(q.Geometry(x,table),offset)
    proof_input=copy.deepcopy(x)
    proof_input['packet']['controller_memory']['last_ctrl']=np.asarray(origin['last_ctrl']).tolist()
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
    candidates=[];records=[]
    for count in [100,200,400,600,800]:
        for target in [-CAP,-.32,-.16,0.,.16,.32,CAP]:
            assert time.monotonic()<fallback_end,'REFUGE_GENERATION_DEADLINE'
            rows=[(float(target),.12,count,0),(0.,0.,2200,0)]
            ss,uu,mm=engine.simulate(origin,rows)
            local=copy.deepcopy(proof_input);local['goal']=ss[-1,:2].tolist()
            proof=q.proof(g,local,ss,uu,q.requests_of(rows),mm)
            pose=ss[-1,:3];guide=np.array([1.72,-1.14,-.67])
            angle=abs(math.atan2(math.sin(pose[2]-guide[2]),math.cos(pose[2]-guide[2])))
            score=float(np.linalg.norm(pose[:2]-guide[:2]))+.2*angle
            record=dict(target=float(target),moving_native=count,passed=proof['passed'],proof=proof,guide_score=score)
            records.append(record)
            if proof['passed']:
                candidates.append(dict(record=record,rows=rows,states=ss,controls=uu,memory=mm,
                    origin=endpoint(origin,ss,mm,True)))
    candidates.sort(key=lambda c:(c['record']['guide_score'],-c['record']['proof']['minimum_raw_m'],
                                  c['record']['moving_native'],c['record']['target']))
    attempts=[];selected=None
    for i,c in enumerate(candidates[:8]):
        if time.monotonic()>=fallback_end:break
        k=len(c['controls'])
        result=search(x,table,min(fallback_end,time.monotonic()+8),checkpoint,
            preview=dict(origin=c['origin'],native_offset=offset+k))
        work+=result['analytical_cpp_native']
        attempts.append(dict(refuge=i,passed=result['passed'],cpp_native=result['analytical_cpp_native']))
        if not result['passed']:continue
        rows=compact(c['rows']+result['rows']);ss,uu,mm=engine.simulate(origin,rows)
        error=max(float(abs(ss[:k+1]-c['states']).max()),float(abs(ss[k:]-result['states']).max()),
            float(abs(uu[:k]-c['controls']).max()),float(abs(uu[k:]-result['controls']).max()),
            float(abs(mm[:k+1]-c['memory']).max()),float(abs(mm[k:]-result['memory']).max()))
        assert error<=1e-8,'CARRIED_ORIGIN_SOURCE_COMPOSITION'
        proof=q.proof(g,proof_input,ss,uu,q.requests_of(rows),mm)
        assert proof['passed'],'FULL_CARRIED_ORIGIN_PROOF'
        selected=dict(rows=rows,states=ss,controls=uu,memory=mm,proof=proof,
            prefix_rows=c['rows'],prefix_native=k,composition_error=error,selected_refuge=i)
        break
    answer=dict(passed=selected is not None,method='refuge_onward',direct_refusal={k:v for k,v in direct.items()if k not in ['states','controls','memory']},
        candidates=records,attempts=attempts,analytical_cpp_native=work+engine.native,
        nominal_preview=True,native_offset=offset,physical_eligible=False)
    if selected is not None:answer.update(selected)
    return answer
