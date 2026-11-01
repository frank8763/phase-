"""Pre-registered saved-input planning only. No simulator/environment import."""
import importlib.util,json,os,sys,time,hashlib
from pathlib import Path
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
sys.path.insert(0,str(repo/'current'))
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0,str(repo/'experiments/v664_dynamic_causal_proposals'))
from exact_footprint import build
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
F=module('dense_edge_frozen_field',repo/'current/footprint_map_b70_v513.py')
old=module('old_sparse_planner',repo/'experiments/v664_dynamic_causal_proposals/planner.py')
new=module('new_dense_planner',src/'planner.py')
out=repo/'runs/v665_dynamic_dense_edges';freeze=json.loads((out/'INPUT_FREEZE.json').read_text())
started=time.monotonic();records=[]
for path,digest in freeze.items():
    p=repo/path;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    plan=json.loads(p.read_text());world=plan['causal_input']
    for name,planner in [('sparse_edges',old),('dense_edges',new)]:
        field=build(F,world);field.guard=.15;field.base_heuristic=F.base._heuristic_grid
        begin=time.monotonic()
        candidate,stats=planner.search(field,plan['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.18,dense_requested_guard=True,work_limit=4000)
        if stats['status']!='GLOBAL_GOAL_PATH':
            preferred=candidate;preferred_stats=stats
            candidate,stats=planner.search(field,plan['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.155,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
            if candidate is None and preferred is not None:candidate,stats=preferred,dict(preferred_stats)
            stats['preferred_search']=preferred_stats
        certificate=None
        if candidate is not None:
            poses=[]
            for a,b in zip(candidate[:-1],candidate[1:]):
                d=b[:3]-a[:3];d[2]=(d[2]+np.pi)%(2*np.pi)-np.pi
                poses.extend(a[:3]+np.arange(6)[:,None]/5*d)
            certificate=float(np.min(field.pose_values(poses)))
            assert certificate>=stats['guard_m']-1e-8,'RETURNED_PATH_CERTIFICATE_FAILED'
        row={'input':path,'variant':name,'stats':stats,'independent_dense_certificate_m':certificate,'path':None if candidate is None else candidate.tolist(),'wall_s':time.monotonic()-begin}
        records.append(row)
        result={'status':'RUNNING','simulation_steps':0,'environment_instances':0,'navigation_tasks':0,'elapsed_s':time.monotonic()-started,'records':records}
        (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
        print(path,name,stats,flush=True)
passed=all(r['path']is not None for r in records if r['variant']=='dense_edges')
result.update(status='SAVED_INPUT_CHECKS_PASS'if passed else'SAVED_INPUT_CHECKS_FAILED',scope='Two saved-input spatial planning checks only; no dynamics, arrival or acceptance claim')
(out/'COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],flush=True)
