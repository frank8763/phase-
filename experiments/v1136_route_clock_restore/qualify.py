"""Actual schedule boundary, prefix identity and saved red repro, zero dynamics."""
import sys,json,ast,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1136_route_clock_restore';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
import numpy as np

def main():
 import importlib.util
 job=O/'qualification_job.json';dump(job,{'output':str(O/'unused')});sys.argv=['qualification',str(job)];spec=importlib.util.spec_from_file_location('actual_worker',C/'worker.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);cases=0;negative=0
 for profile in json.loads((C/'PROFILES.json').read_text()):
  source=json.loads((R/profile['seed_file']).read_text());base=source['rows'];base=base[1:]if len(base)==56 else base;angles=[r[0]for r in base[42:54]]
  for duration in [.4,1.,1.8]:
   for wait in [0.,19.63]:
    u=np.r_[angles,np.full(12,duration),wait];rows,n=w.schedule(base,u,profile['speed']);body=rows[1:]if n else rows;assert body[:41]==[tuple(r)for r in base[:41]];assert body[-1]==(0.,0.,2200,0);assert all(r[2]==600 for r in body if r[3]);assert [r[1]for r in body[42:54]]==[profile['speed']]*12;cases+=1
  for i,value in [(0,.428),(12,.399),(12,1.801),(24,19.64),(24,-.01)]:
   u=np.r_[angles,np.ones(12),0.];u[i]=value
   try:w.schedule(base,u,profile['speed'])
   except AssertionError:negative+=1
   else:raise AssertionError('BOUNDARY_NEGATIVE_ACCEPTED')
 # Unequal durations change actual commands and must not be a metadata-only timing change.
  u=np.r_[angles,np.linspace(.6,1.4,12),1.];rows,n=w.schedule(base,u,profile['speed']);assert len(set(r[2]for r in rows[-13:-1]))>1
 old=json.loads((R/'runs/v1135_causal_batch/saved_v80/OPTIMIZATION.json').read_text());assert not old['proof']['passed'] and not old['proof']['checks']['full_raw_geometry'];assert old['minimum_timed_dynamic_m']<w.REQUIRED
 for p in C.glob('*.py'):ast.parse(p.read_text())
 answer={'passed':True,'actual_worker_entry_imported':True,'schedule_boundary_cases':cases,'out_of_range_rejected':negative,'all_first41_commands_preserved':True,'all2200_tails_and600_modes_preserved':True,'nonuniform_duration_affects_executable_commands':True,'saved_failure_still_red':True,'functional_fix_claimed':False,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':0};dump(O/'QUALIFICATION.json',answer);print(json.dumps(answer))
if __name__=='__main__':main()
