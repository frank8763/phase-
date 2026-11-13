"""Mixed mode dynamics agreement, causal origin and fixed schedule checks."""
import sys,json,ast,subprocess,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1109_joint_cusp_source'
sys.path.insert(0,str(C));import run as driver
import numpy as np
from solver import Solver,CAP
def main():
 O.mkdir(parents=True,exist_ok=True)
 for p in C.glob('*.py'):ast.parse(p.read_text())
 target=O/'profile.so'
 if not target.exists():subprocess.run(['g++','-std=c++17','-O3','-fPIC','-shared',str(C/'profile.cpp'),'-o',str(target)],check=True,timeout=30)
 x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());engine=Solver(x,np.array(pg['path']),pg['gear']);maximum=0.;cpp_count=0;python_count=0;cases=0
 def accelerated(rows):
  nonlocal cpp_count
  n=sum(r[2]for r in rows);s=np.empty((n,8));u=np.empty((n,4));targets=np.array([r[0]for r in rows],float);speeds=np.array([r[1]for r in rows],float);ticks=np.array([r[2]for r in rows],np.int32);modes=np.array([r[3]for r in rows],np.int32)
  code=engine.lib.profile(engine.state,engine.memory,targets,speeds,ticks,modes,len(rows),engine.limits,engine.rates,engine.parameters,s,u)
  if code==n:cpp_count+=n
  return code,np.vstack([engine.state,s]),u
 for speed in [.08,-.03]:
  for angle in np.linspace(-CAP,CAP,5):
   rows=[(float(angle),speed,500,0)];code,s,u=accelerated(rows);assert code==500;ss,uu,*_=driver.replay_rows(x,rows);maximum=max(maximum,float(abs(s-ss).max()),float(abs(u-uu).max()));python_count+=500;cases+=1
 rows=[(-CAP,-.03,250,0),(0.,0.,2200,0),(CAP,0.,300,1),(CAP,.08,100,0),(0.,0.,2200,0),(-CAP,0.,300,1)]
 code,s,u=accelerated(rows);assert code==5350;ss,uu,rr,memory,modes,targets=driver.replay_rows(x,rows);maximum=max(maximum,float(abs(s-ss).max()),float(abs(u-uu).max()));python_count+=code;assert maximum<=1e-8,'MIXED_MODE_CPP_PYTHON_MISMATCH'
 assert np.array_equal(uu[modes==1,2:],np.zeros((int((modes==1).sum()),2)))
 code,*_=accelerated([(CAP+.01,0.,1,1)]);assert code==201,'OUTSIDE_CAP_MODE_ACCEPTED'
 old=engine.memory.copy();engine.memory[2:4]=.001;code,*_=accelerated([(0.,0.,1,1)]);engine.memory=old;assert code==201,'NONZERO_REAR_MODE_ACCEPTED'
 z=engine.seed();assert len(z)==52 and np.all(z>=engine.lower)and np.all(z<=engine.upper);rows,sections=engine.schedule(z)
 assert len(sections)==4 and all(end-moving==2200 for begin,moving,end in sections);assert sum(r[3]==1 for r in rows)==3
 assert all(rows[i-1][2]==2200 and rows[i-1][1]==0. for i,row in enumerate(rows)if row[3])
 refused=[]
 for name in ['mujoco','physical','vehicle','factory','torch','rclpy']:
  try:__import__(name)
  except AssertionError:refused.append(name)
 assert len(refused)==6
 q=dict(passed=True,ordinary_cases=cases,mixed_mode_rows=6,maximum_cpp_python_error=maximum,rear_zero_parked_mode=True,negative_cases=['outside_steering_cap','nonzero_rear'],schedule_variables=52,complete_stops=4,parked_blocks=3,imports_refused=refused,analytical_work=dict(cpp_native=cpp_count,python_native=python_count),binary_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),models=0,physical_integrations=0)
 (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q))
if __name__=='__main__':main()
