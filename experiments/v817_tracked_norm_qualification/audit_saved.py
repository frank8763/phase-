"""Independent two saved contracts plus fixed mathematical boundary checks."""
import hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
own=Path(__file__).parent;repo=own.parents[1];root=repo/'runs/v817_tracked_norm_qualification'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('INDEPENDENT_NORM_AUDIT_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(repo/'experiments/v812_soft_global_reference'));sys.path.insert(0,str(own))
from exact_footprint import pose_values
from independent_norm import radial_lower,static_field
from motion_evaluator import check_forecast
from union_belief import future_cells
from types import SimpleNamespace
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(repo/n)==h for n,h in read(own/'CANDIDATE_FREEZE.json')['files'].items())
protocol=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/STATIC_PROTOCOL.json');config=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/DYNAMIC_PROTOCOL.json')
base=static_field(protocol);rows=read(root/'RESULTS.json');records=[];coverage=0
for row in rows:
    z=np.load(root/f'step{row["step"]:04d}.npz');entry=row['original_input'];state=entry['state'];radial=radial_lower(base,z['poses'],state,z['times'])
    static=pose_values(base,z['poses']);expected=np.maximum(z['old_values'],np.minimum(static,radial))
    error=float(np.max(abs(expected-z['new_values'])));radial_error=float(np.max(abs(radial-z['radial_values'])))
    checks=dict(frozen_source=sha(repo/entry['source_file'])==entry['source_sha256'],witness=sha(repo/entry['witness_file'])==entry['witness_sha256'],independent_full_geometry=error<=1e-10 and radial_error<=1e-10,
        all_native_samples=len(z['new_values'])==328,gate_preserved=float(z['new_values'].min())>=.155,
        original_self=entry['self_domain_margin_m']>=.002,original_terminal_speed=entry['terminal_speed_m_s']<=.025,
        monotone_bound=bool(np.all(z['new_values']>=z['old_values']-1e-12)),static_not_removed=bool(np.all(z['new_values']<=static+1e-12)),no_truth=state['hidden_world_geometry_used']is False,
        original_329_coverage=check_forecast(config,state)['passed'])
    t=np.arange(657)*.01;lo,hi=future_cells(state['outer_state_cells'],t)
    truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+t)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    checks['original_657_coverage']=bool(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max()<=1e-7)
    # Evaluator only: true present centre lies in at least one current cell;
    # its future displacement is within the public .08*dt ball. The config
    # values below are NEVER arguments of radial_lower or the online gate.
    cells=np.asarray(state['outer_state_cells']);present=truth[0]
    current_excess=float(np.maximum(cells[:,0]-present,present-cells[:,1]).max(axis=1).min())
    displacement=np.linalg.norm(truth-present,axis=1);norm_excess=float((displacement-.08*t).max())
    checks['declared_norm_coverage']=current_excess<=1e-7 and norm_excess<=1e-7
    coverage+=329+657
    records.append(dict(step=row['step'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values())),maximum_independent_error=error,maximum_radial_error=radial_error,current_cell_excess=current_excess,norm_displacement_excess=norm_excess))
# Fixed boundaries: the .08 norm contract supports axial and diagonal motion
# at .08, while a .12 axial motion is explicitly outside this smaller class.
directions=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)]
dt=np.array([0.,.01,.08,.8,3.28,6.56]);distance=np.linalg.norm(dt[:,None,None]*.08*directions[None],axis=2)
math_checks=dict(public_norm_bound_retains_all_fixed_directions=bool(np.all(distance<=.08*dt[:,None]+1e-12)),
    broader_axis_class_explicitly_not_claimed=bool(np.linalg.norm(np.array([.12,0.])*3.28)>.08*3.28),
    class_is_declared_in_prior_course=abs(config['maximum_speed_m_s']-.08)<1e-12,
    input_scopes_fixed=[r['step']for r in rows]==[586,598])
passed=bool(all(math_checks.values())and all(r['passed']for r in records))
result=dict(status='DECLARED_NORM_FIXED_CONTRACTS_INDEPENDENT_PASS'if passed else'DECLARED_NORM_FIXED_QUALIFICATION_NOT_PASSED',records=records,mathematical_boundary_checks=math_checks,
    original_329_plus_657_samples=coverage,new_models=0,new_integrations=0,
    scope='Original full saved controls and public norm-motion mathematical refinement only. Actual native state/control reproduction and real branch safety still required before navigation; wider .12/axis class not covered.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if passed else 1)
