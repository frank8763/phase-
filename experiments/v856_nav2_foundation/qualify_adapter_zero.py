"""Actuator map integration seam checks, no simulator import/initialization."""
import json,sys
from pathlib import Path
import numpy as np
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;sys.path.insert(0,str(R/'experiments/v855_renewal_worker'))
from vehicle_control import Adapter
class Names:
    @staticmethod
    def mj_name2id(m,kind,name):return ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act'].index(name)
    mjtObj=SimpleNamespace(mjOBJ_ACTUATOR=0)
m=SimpleNamespace(actuator_ctrllimited=np.ones(4),actuator_ctrlrange=np.array([[-.52,.52],[-.52,.52],[-20.,20.],[-20.,20.]]));a=Adapter(m,Names);rows=[]
for v,w,mv,mw,stale in [(0.,0.,0.,0.,False),(.3,.24,.0,.0,False),(-.15,.24,0.,0.,False),(.2,float('inf'),0.,0.,False),(.2,.1,.2,.1,True)]:
    previous=a.last.copy()
    if not np.isfinite([v,w,mv,mw]).all():
        try:a.compute(v,w,mv,mw,stale)
        except AssertionError:rows.append({'nonfinite_rejected':True});continue
        raise AssertionError('NONFINITE_ACCEPTED')
    command=a.compute(v,w,mv,mw,stale);rows.append({'legal':bool(a.commands.legal(command)),'slew':bool(np.all(abs(command-previous)<=a.commands.rate*.01/.08+1e-12)),'stale':stale})
assert len(rows)==5 and all(all(v for k,v in r.items()if k!='stale')for r in rows)
p=R/'runs/v856_nav2_foundation/ZERO_ADAPTER_QUALIFICATION.json';p.write_text(json.dumps(dict(passed=True,rows=rows,model_initializations=0,integrations=0,scope='synthetic actuator limits only; actual native dynamics still untested'),indent=2)+'\n');print(p)
