"""Current-mocap sensor-only geometry, no phase/future actor API accepted."""
import math,os
from pathlib import Path

def world_from_arrays(np,measured,known,arrays,ids):
 assert set(ids)=={'mocap_id','geom_id','radius_m','cylinder_type'}and ids['radius_m']==.1
 assert set(arrays)=={'mocap_pos','mocap_quat','geom_size','geom_type','geom_bodyid','body_mocapid','geom_pos'}
 k=measured['native'];assert type(k)is int and abs(measured['sim_time']-.01*k)<=1e-8
 mid=ids['mocap_id'];gid=ids['geom_id'];body=int(arrays['geom_bodyid'][gid]);assert int(arrays['body_mocapid'][body])==mid and int(arrays['geom_type'][gid])==ids['cylinder_type']
 assert float(arrays['geom_size'][gid,0])==ids['radius_m']and np.array_equal(arrays['geom_pos'][gid,:2],np.zeros(2))
 quat=np.asarray(arrays['mocap_quat'][mid]);assert abs(float(quat[0]))==1. and np.array_equal(quat[1:],np.zeros(3))
 xy=np.asarray(arrays['mocap_pos'][mid,:2],float);assert np.isfinite(xy).all()
 return dict(native=k,sim_time=measured['sim_time'],bounds=[-5.,5.],rectangles=[list(x)for x in known['known_rectangles']],circles=[list(x)for x in known['known_circles']]+[[float(xy[0]),float(xy[1]),.1]])
def live(np,v,receipt,known,ids,task,source,binding):
 # Reject before ANY live object/model access when not source-admitted.
 from context import admission,sha,R,C
 admission(task);assert os.sched_getaffinity(0)=={2}and source[str((C/'private_snapshot.py').relative_to(R))]==sha(C/'private_snapshot.py')
 p=receipt['packet'];assert v.count==p['native_tick']and float(v.d.time)==p['sim_time']and list(v.body())==p['body']
 arrays={n:np.asarray(getattr(v.d,n)).copy()for n in ['mocap_pos','mocap_quat']};arrays.update({n:np.asarray(getattr(v.m,n)).copy()for n in ['geom_size','geom_type','geom_bodyid','body_mocapid','geom_pos']})
 return world_from_arrays(np,dict(native=v.count,sim_time=float(v.d.time),body=p['body']),known,arrays,ids)
