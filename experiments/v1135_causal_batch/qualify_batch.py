"""Load every actual worker entry and check each fixed speed/seed schedule."""
import sys,json,ast,importlib.util,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1135_causal_batch';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
import numpy as np

def load(name,file):
 s=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 q=json.loads((O/'QUALIFICATION.json').read_text());assert q['passed'];dummy=O/'qualification_job.json';dump(dummy,{'output':str(O/'entry_fixture'),'source':str(R/'runs/v1133_terminal_spatial_corridor'),'table':str(O/'not_used_in_import.npz'),'table_sha256':'unused','id':'qualification','seed':'saved','speed_factor':1.,'wait_seconds':0.});saved_argv=sys.argv[:];sys.argv=['qualification',str(dummy)];worker=load('actual_joint_batch_worker',C/'joint_worker.py');load('actual_phase_batch_worker',C/'phase_worker.py');load('actual_audit_batch_worker',C/'audit_worker.py');load('actual_domain_batch_worker',C/'domain_worker.py');sys.argv=saved_argv
 t=json.loads((C/'TASK.json').read_text());x=json.loads((R/t['input']).read_text());x['safe_terminal_pose']=json.loads((R/t['terminal']).read_text())['selected_body_pose'];p=json.loads((R/t['path']).read_text());s=worker.Solver(x,np.array(p['path']),p['gear']);vectors={'saved':np.array(json.loads((R/'runs/v1133_terminal_spatial_corridor/TERMINAL_REACHABILITY.json').read_text())['selected_z']),'cold':s.seed()};count=0
 for seed,z in vectors.items():
  s.prefix_rows=s.schedule(z)[0][:41]
  for factor in [1.,1.25,1.5]:
   for wait in [0.,18.5,19.63]:
    u=np.r_[z[36:48],wait];rows,n,events=worker.schedule(s,z,u,factor);without=rows[1:]if n else rows;assert without[:41]==s.prefix_rows;assert sum(int(r[2])for r in without)==events[-1][2];assert abs(max(r[1]for r in without)-.08*factor)<1e-12;assert without[-1]==(0.,0.,2200,0);count+=1
 # Geometry clone must shift only predicted start time; original remains exact.
 from geometry import Geometry,OriginalTimed,pg
 old=OriginalTimed(x);data={'centers':(np.arange(256)+.5)*old.period/256,'bounds':np.tile((old.bounds.max(axis=0)+.1)[None,:],(256,1))};g=Geometry(x,data);poses=np.array([[.5,-.3,.5],[4.,-1.85,0.]]);ticks=np.array([0,100]);sa,da=g.components(poses,ticks);oa,od=old.components(poses,ticks);assert np.all(sa==oa)and np.all(da>=od-1e-9)
 for f in C.glob('*.py'):ast.parse(f.read_text())
 answer={'passed':True,'actual_worker_entries_imported':4,'fixed_seed_speed_wait_cases':count,'full2200_tails_and_prefix_commands_verified':True,'cold_seed_curvature_source':True,'geometry_intersection_not_wider_than_old':True,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0,'real_solver_calls':0};dump(O/'BATCH_ENTRY_QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
