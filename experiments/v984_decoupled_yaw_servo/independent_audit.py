"""Independent scalar projection and tampering audit of saved map witnesses."""
import copy,json,math
from pathlib import Path
from control_fixture import R
O=R/'runs/v984_decoupled_yaw_servo'

def check(row):
    p=row['proof'];u=row['counterfactual_control'];n=p['nominal'];prev=p['previous']
    assert all(math.isfinite(x)for x in u+n+prev)
    assert max(abs(u[i]-n[i])for i in [0,1])<=1e-12
    rates=[.0125,.0125,.0875,.0875];limits=[.52,.52,20.,20.]
    assert all(abs(u[i])<=limits[i]+1e-10 and abs(u[i]-prev[i])<=rates[i]+1e-10 for i in range(4))
    if not p['applied']:
        assert max(abs(a-b)for a,b in zip(u,n))<=1e-12;return
    mean=(n[2]+n[3])/2
    assert abs((u[2]+u[3])/2-mean)<=1e-12
    bounds=[]
    for i in [2,3]:
        a=max(-20.,prev[i]-.0875);b=min(20.,prev[i]+.0875)
        if n[i]>0:a=max(a,0.)
        elif n[i]<0:b=min(b,0.)
        else:a=b=0.
        bounds.append((a,b))
    # Eliminate left=mean-d, right=mean+d from the four inequalities.
    a=max(mean-bounds[0][1],bounds[1][0]-mean)
    b=min(mean-bounds[0][0],bounds[1][1]-mean)
    v=max(-.15,min(.30,p['requested'][0]));k=math.tan(.42722137342572125)/.6
    w=max(-abs(v)*k,min(abs(v)*k,p['requested'][1]))
    requested=max(-.16,min(.16,w+1.5*(w-p['measured'][1])))*.54/.24
    optimum=min(b,max(a,requested))
    assert abs(u[2]-(mean-optimum))<=1e-12 and abs(u[3]-(mean+optimum))<=1e-12
    assert abs(p['selected_differential']-optimum)<=1e-12

def main():
    q=json.loads((O/'CONTROL_MAP_QUALIFICATION.json').read_text());rows=q['saved_feedback_witnesses']
    for row in rows:check(row)
    negatives=[]
    for label,mutate in [
        ('front_override',lambda r:r['counterfactual_control'].__setitem__(0,r['counterfactual_control'][0]+.001)),
        ('common_speed_override',lambda r:r['counterfactual_control'].__setitem__(3,r['counterfactual_control'][3]+.01)),
        ('differential_sign_swap',lambda r:r['counterfactual_control'].__setitem__(slice(2,4),list(reversed(r['counterfactual_control'][2:])))),
        ('false_feedback_measurement',lambda r:r['proof']['measured'].__setitem__(1,.06)),
        ('false_proof',lambda r:r['proof'].__setitem__('selected_differential',0.)),
        ('rate_violation',lambda r:r['counterfactual_control'].__setitem__(2,10.)),
        ('nonfinite',lambda r:r['counterfactual_control'].__setitem__(2,float('nan')))
    ]:
        row=copy.deepcopy(next(r for r in rows if r['proof']['applied']and not r['proof']['projection_limited']));mutate(row)
        try:check(row)
        except AssertionError:negatives.append(dict(case=label,rejected=True))
        else:negatives.append(dict(case=label,rejected=False))
    result=dict(passed=all(n['rejected']for n in negatives),models=0,integrations=0,
        independent_saved_witnesses=len(rows),negative_cases=negatives,physical_tracking_qualified=False,
        scope='Independent commanded-target amplitude/slew/common/front/projection checks only; no plant response or physical tracking claim')
    (O/'INDEPENDENT_CONTROL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
