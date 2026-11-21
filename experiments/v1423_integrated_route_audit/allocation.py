"""Independent original allocator replay inside existing CPU2 native owner."""
import fcntl
import math
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2]

def audit(vehicle,rows,initial,*,Adapter,mj,np,lock,maximum_recomputations,deadline_unix,deadline_monotonic):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
 assert len(rows)==len(vehicle.rows)<=maximum_recomputations
 cursor=[None];owner=Adapter(vehicle.m,mj,vehicle.dt,encoders=lambda:np.asarray(cursor[0]['encoders']));owner.virtual_rate=.6;owner.last=np.asarray(initial['controller_memory']['last_ctrl']);owner.integral=initial['controller_memory']['integral'];owner._steering_motion_active=False
 maximum=0.;computed=0
 for i,row in enumerate(rows):
  assert time.time()<deadline_unix and time.monotonic()<deadline_monotonic and row['before_native']==i and row['applied']
  cursor[0]=row;maximum=max(maximum,float(abs(owner.last-np.asarray(row['last_ctrl'])).max()),abs(owner.integral-row['integral']))
  assert maximum<=1e-8,'ALLOCATOR_MEMORY_REPLAY_DIVERGED'
  owner.parked_target=row['parked_target'];u=owner.compute(*row['request'][:2],*row['body'][3:],False);computed+=1
  maximum=max(maximum,float(abs(u-vehicle.rows[i]['ctrl'][vehicle.adapter.commands.ids]).max()));assert maximum<=1e-8,'ALLOCATOR_CONTROL_REPLAY_DIVERGED'
 return dict(passed=True,recorded_rows=len(rows),allocator_recomputations=computed,explicit_allocator_constructions=1,mujoco_models_created=0,physical_native=0,analytical_integrations=0,maximum_memory_control_error=maximum)
