"""Bounded next-step hypothesis: complete timed crossing, same safety gates."""
import sys,json,importlib.abc,time,signal,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np,corridor
from kernel import Geometry,REQUIRED,checks,ref
def main():
    assert not(O/'TIMED_HYPOTHESIS.json').exists()
    def halt(*_):raise TimeoutError('120S_ZERO_MODEL_TIMED_HYPOTHESIS')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120)
    started=time.monotonic();rows=[]
    try:
        x=json.loads((O/'FAILED_ACTUAL_INPUT.json').read_text());setup=x['setup'];packet=x['packet'];source=x['source']
        static=corridor.planner(O).construct(setup,packet,None,x['goal'],wall_s=30.,max_expansions=20000)
        assert static['passed']and static['functional_goal_source']
        rr=np.array(static['planned_body_requests']);assert not np.any(rr[:,0]<0),'SINGLE_FORWARD_CROSSING_REQUIRED'
        rr=np.vstack([rr,np.zeros((2000,3))]);accepted=None
        for wait in range(0,1964,125):
            requests=np.vstack([np.zeros((wait,3)),rr]);states,controls,_=corridor.live.run_requests(setup,packet,requests)
            low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(states)
            gates,goal=checks(states,controls,requests,packet,setup,np.asarray(x['goal']),low,REQUIRED)
            a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(states[-1:,:3])
            gates.update(terminal_full_cycle_hold=bool(min(a[0],b[0])>=REQUIRED),complete2200stop=np.array_equal(requests[-2200:],np.zeros((2200,3))))
            row=dict(wait_native=wait,passed=bool(all(gates.values())),minimum_timed_raw_m=low,goal_upper_m=goal,checks={k:bool(v)for k,v in gates.items()});rows.append(row)
            if row['passed']:
                accepted=row;np.savez_compressed(O/'TIMED_HYPOTHESIS_PLAN.npz',states=states,controls=controls,requests=requests);break
        answer=dict(hypothesis_has_nominal_full_goal_certificate=accepted is not None,accepted=accepted,candidates=rows,
                    static_actions=static['actions'],source_from_actual_ranges=True,models=0,integrations=0,
                    physical_authorized=False,not_a_physical_or_robust_qualification=True,wall_s=time.monotonic()-started)
    except BaseException as error:answer=dict(hypothesis_has_nominal_full_goal_certificate=False,error=repr(error),traceback=traceback.format_exc(),candidates=rows,models=0,integrations=0,physical_authorized=False,wall_s=time.monotonic()-started)
    signal.setitimer(signal.ITIMER_REAL,0);(O/'TIMED_HYPOTHESIS.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
