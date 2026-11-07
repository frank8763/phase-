"""Three fixed saved causal global searches with renewal-cost proposal; no models."""
import hashlib,importlib.abc,json,signal,sys,time
from pathlib import Path
from types import MethodType,SimpleNamespace
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('REFERENCE_PROBE_NO_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OLD=R/'experiments/v853_maneuver_worker';sys.path.insert(0,str(OLD));sys.path.insert(0,str(R/'current'));sys.path.insert(0,str(R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
import numpy as np
from independent_soft_reference import field,dense_path
from current_guide import attach
from planner import spatial_search
from renewal_cost import deficit,EDGE_WEIGHT


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ZERO_MODEL_REFERENCE_240S')));signal.alarm(240);root=R/'runs/v855_renewal_progress';out=root/'reference_probe04';out.mkdir(exist_ok=False);pair=R/'runs/v853_maneuver_worker/v853_B64_main_slot01/paired';protocol=json.loads((pair/'STATIC_PROTOCOL.json').read_text());cell=pair/'geometry_memory';states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};rows=[]
    for step in [303,533,936]:
        saved=json.loads((cell/f'planning_{step:04d}.json').read_text())if(cell/f'planning_{step:04d}.json').exists()else max((json.loads(p.read_text())for p in cell.glob('planning_*.json')if json.loads(p.read_text())['step']<=step),key=lambda p:p['step'])
        state=states[step];f=field(protocol,state);f.pose_values=MethodType(__import__('exact_footprint').pose_values,f);f.config=SimpleNamespace(**vars(f.config))
        # The independently constructed geometric field lacks a search grid;
        # build the original grid from the exact saved causal input only.
        from footprint_map_b70_v513 import FootprintMap
        original=FootprintMap(saved['causal_route_input']);f=original;f.pose_values=MethodType(__import__('exact_footprint').pose_values,f);f.base_heuristic=__import__('footprint_map_b70_v513').base._heuristic_grid
        attach(f,state);old=f.soft_forecast_cost
        def cost(self,poses):return EDGE_WEIGHT*np.maximum(old(poses),deficit(self,state,poses))
        f.soft_forecast_cost=MethodType(cost,f)
        trace=json.loads((cell/'trace.json').read_text());q=trace[step-1]['pose'];started=time.monotonic();path,stats=spatial_search(f,q,protocol['goal_xy'],.60,.42722137342572125,guard=.155,budget=2,resolution=.1,heading_bins=72,dense_requested_guard=True,work_limit=4000,forward_only=True)
        row=dict(step=step,stats=stats,wall_s=time.monotonic()-started,path=None if path is None else path.tolist(),causal_state=state,goal_xy=protocol['goal_xy'],renewal_cost_only=True)
        if path is not None:row.update(max_renewal_deficit=float(deficit(f,state,path[:,:3]).max()),minimum_current_clearance=float(f.pose_values(dense_path(path)).min()))
        rows.append(row);(out/f'step{step:04d}.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({k:v for k,v in row.items()if k not in ['path','causal_state']}),flush=True)
    (out/'RESULT.json').write_text(json.dumps(dict(records=[{k:v for k,v in row.items()if k not in ['path','causal_state']}for row in rows],models=0,integrations=0),indent=2)+'\n')


if __name__=='__main__':main()
