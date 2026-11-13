"""Causal dynamic occupancy affects the topology proposer, zero physics."""
import sys,json,copy,time,signal,traceback,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1092_stopped_replan'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np,corridor
from cycle_backup import cycle_upper
from polygon_geometry import polygon
def main():
    assert not(O/'SPATIAL_HYPOTHESIS.json').exists()
    def halt(*_):raise TimeoutError('120S_SPATIAL_HYPOTHESIS')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120);start=time.monotonic()
    try:
        x=json.loads((O/'FAILED_ACTUAL_INPUT.json').read_text());poly=polygon(cycle_upper(x['source']['periodic']))
        box=np.r_[poly.min(axis=0)-.1,poly.max(axis=0)+.1]
        encoded=np.r_[(box[:2]+box[2:])/2,(box[2:]-box[:2])/2]
        assert np.all(encoded[2:]>0)and np.allclose(np.r_[encoded[:2]-encoded[2:],encoded[:2]+encoded[2:]],box)
        setup=copy.deepcopy(x['setup']);setup['known']['known_rectangles'].append(encoded.tolist())
        # This extra rectangle exists only in the proposer, not the world,
        # original static map contract or independent certificate geometry.
        static=corridor.planner(O).construct(setup,x['packet'],None,x['goal'],wall_s=30.,max_expansions=20000)
        answer=dict(full_cycle_center_polygon=poly.tolist(),proposer_only_dynamic_outer_box=box.tolist(),proposer_center_half_extents=encoded.tolist(),
                    physical_scene_changed=False,actual_static_entities_unchanged=True,
                    static={k:static.get(k)for k in ['passed','functional_goal_source','expanded','status','minimum_raw_m','terminal_goal_upper_m','actions']})
        if static['passed']and static['functional_goal_source']:
            rr=np.array(static['planned_body_requests']);requests=np.vstack([rr,np.zeros((2000,3))])
            proof,states,controls=corridor.proof(x['setup'],x['packet'],x['source'],requests)
            answer.update(original_full_cycle_certificate=proof,
                          actual_original_goal_predicted_distance_m=float(np.linalg.norm(states[-1,:2]-x['goal'])))
            np.savez_compressed(O/'SPATIAL_HYPOTHESIS_PLAN.npz',requests=requests,states=states,controls=controls)
        answer.update(models=0,integrations=0,physical_authorized=False,not_a_complete_physical_qualification=True,wall_s=time.monotonic()-start)
    except BaseException as error:answer=dict(error=repr(error),traceback=traceback.format_exc(),models=0,integrations=0,physical_authorized=False,wall_s=time.monotonic()-start)
    signal.setitimer(signal.ITIMER_REAL,0);(O/'SPATIAL_HYPOTHESIS.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
