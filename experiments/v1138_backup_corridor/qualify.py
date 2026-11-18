import sys,subprocess
from corridor_tools import *

def main():
 assert not (O/'DRIVER_STARTED.json').exists();subprocess.run(['g++','-std=c++17','-O3','-shared','-fPIC',str(C/'connect.cpp'),'-o',str(O/'configuration.so')],check=True,timeout=30);lib=library();bounds=np.ones(16)*.1
 r,p=graph(lib,[],[],bounds,[-1.,0.,0.],[1.,0.],False,.2,8,5.);assert r['found']and np.linalg.norm(p[-1,:2]-[1.,0.])<=.025 and abs(np.arctan2(np.sin(p[-1,2]),np.cos(p[-1,2])))<=.1
 for wall in [.1,.001]:
  r,p=graph(lib,[[0.,0.,wall,5.]],[],bounds,[-1.,0.,0.],[1.,0.],False,.2,8,5.);assert r['code']==1
 src=json.loads((R/'runs/v1136_route_clock_restore/dynamic_seed_v120/OPTIMIZATION.json').read_text());rows=prefix(src['rows'],12500);assert sum(r[2]for r in rows)==14700 and rows[-1]==(0.,0.,2200,0)
 for cut in [1,956,3626,6571,10344,12500]:
  rows=prefix(src['rows'],cut);assert sum(r[2]for r in rows)==cut+2200 and rows[-1]==(0.,0.,2200,0)
 anchor=np.load(R/'runs/v1136_route_clock_restore/dynamic_seed_v120/SELECTED_SOURCE.npz')['states'][12500,:3];assert 1.65<=anchor[0]<=1.95 and -1.6<=anchor[1]<=-1.2 and -1.1<=anchor[2]<=-.5
 import importlib.util
 spec=importlib.util.spec_from_file_location('actual_corridor_run',C/'run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);assert callable(m.main)
 q={'actual_driver_entry_imported':True,'fixed_refuge_region_verified':True,'passed':True,'actual_cpp_free_graph_and_target_heading':True,'sealed_and_thin_wall_rejected':True,'fixed_prefix_boundaries_verified':6,'binary_sha256':sha(O/'configuration.so'),'models':0,'analytical_dynamics_integrations':0,'physical_integrations':0,'new_optimizer_calls':0};dump(O/'QUALIFICATION.json',q);print(json.dumps(q))
if __name__=='__main__':main()
