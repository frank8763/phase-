"""Saved real trace counterexample, early hold and outward-escape negatives."""
import json
from pathlib import Path
import numpy as np
from recovery_guard import check, EARLY_MARGIN
from observed_route import revalidate

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    raw=R/'runs/v858_nav2_verified/v1347/rpp_async_default_dynamic_main'
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    j=json.loads((raw/'APPLIED_JOURNAL.json').read_text());caught=None
    for tick in range(13965,15415,5):
        row=j[tick];ok,proof=check(known,row['body'],*row['request'][:2])
        if not ok:
            caught=dict(native=tick,body=row['body'],request=row['request'],proof=proof);break
    assert caught and caught['native']<15267 and caught['proof']['current_known_clearance_m']>.24
    # At the actual first recovery-margin loss, old policy still requested
    # forward; new policy denies it rather than relaxing the22cm route gate.
    row=j[15267];assert not check(known,row['body'],*row['request'][:2])[0]
    # Generate an explicit synthetic stopped boundary state from an original
    # measured pose; a short reverse command increases known-map clearance.
    body=caught['body'][:];body[3:]=[0.,0.]
    outward,op=check(known,body,-.05,0.)
    assert outward,op
    assert check(known,body,0.,0.)[0]
    later=j[15365]['body'][:];later[3:]=[0.,0.]
    assert not check(known,later,-.05,0.)[0], 'BELOW_RECOVERY_GATE_MUST_NOT_BE_CALLED_RECOVERABLE'
    # Full unchanged latest-field validation on two actual new planner outputs.
    paths=[]
    for index in [4,5]:
        req=json.loads((raw/'planner_jobs'/('request%02d.json'%index)).read_text())
        res=json.loads((O/('CURVATURE_PROBE%02d.json'%index)).read_text())
        p=np.asarray(res['path']);assert len(p)>=20
        diff=np.diff(p[:,:3],axis=0);arc=np.linalg.norm(diff[:,:2],axis=1)
        angle=np.arctan2(np.sin(diff[:,2]),np.cos(diff[:,2]))
        # Chord ratio slightly exceeds continuous curvature; bound by exact
        # circular arc geometry rather than silently labelling it violation.
        chord_bound=2*np.sin(.5*.04/2)/.5
        assert np.max(abs(angle))<=.5*.04+1e-10 and arc.min()>=chord_bound-1e-10
        ok,proof=revalidate(known,res['path'],req['body'],(req['ball'][:2],req['ball'][2]),.22)
        assert ok,proof
        paths.append(dict(saved_request=index,geometry=proof,full_goal_reached=res['report']['status']=='GLOBAL_GOAL_PATH'))
    proof=dict(passed=True,exact_saved_loss_request_denied=True,first_early_hold=caught,
               stopped_outward_preview_allowed=op,below_recovery_margin_not_admitted=True,
               qualified_new_paths=paths,nominal_curvature_m_inv=.50,
               execution_curvature_m_inv=1/1.32,physical_braking_not_tested=True,
               synthetic_stopped_feedback_explicit=True,models=0,physical_native=0)
    (O/'RECOVERY_RESERVE_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
