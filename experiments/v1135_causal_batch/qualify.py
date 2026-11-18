"""Containment and dual bounds, actual prior identity; no dynamics or physics."""
import sys,json,itertools,hashlib,ast,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1135_causal_batch';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(C));from joint_domain import Domain,NORMALS
import numpy as np

def main():
 center=np.array([3.,.12,.03,-1.,.02,.18]);points=center+np.array(list(itertools.product([-.01,.01],repeat=6)));vertices=[]
 for n in NORMALS[:8]:vertices.append((points[:,:3]*n[0]+points[:,3:]*n[1]).tolist())
 d=Domain(vertices);assert np.all(points@d.A.T<=d.b+1e-10);rng=np.random.default_rng(1135);max_gap=-np.inf
 for _ in range(32):
  w=rng.normal(size=6);bound,lam,res=d.certified_upper(w);known=float((points@w).max());assert bound>=known-1e-9;max_gap=max(max_gap,bound-known);certificate=float(d.b@lam+np.where(res>=0,res*d.upper,res*d.lower).sum()+1e-8);assert abs(bound-certificate)<1e-10
 x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());actual=Domain(x['source']['periodic']['vertices']);assert np.max(actual.A@actual.witness-actual.b)<1e-7;bounds,duals,residual=actual.table([0.,3.]);assert np.isfinite(bounds).all();assert np.all(duals>=0);np.savez_compressed(O/'QUALIFIED_DOMAIN.npz',A=actual.A,b=actual.b,lower=actual.lower,upper=actual.upper,witness=actual.witness);answer={'passed':True,'synthetic_contained_6d_vertices':64,'dual_support_cases':32,'max_guarded_gap_over_true_synthetic_max':float(max_gap),'actual_domain_nonempty':True,'actual_inequalities':len(actual.b),'actual_support_cases':32,'max_dual_residual':actual.max_residual,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'qualification_lp_calls':d.calls+actual.calls};dump(O/'QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
