"""Lossless current prefix first; never integrate or reconstruct contact rows."""
import hashlib
from pathlib import Path
FIELDS=('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')
def save_current_prefix(vehicle,initial,output,quota,np):
 output=Path(output);n=len(vehicle.rows);assert type(vehicle.count)is int and n<=vehicle.count
 assert set(initial)==set(FIELDS)and np.asarray(initial['time']).shape==(),'INITIAL_FULL_STATE_TIME_MUST_BE_SCALAR'
 expected={k:np.asarray(initial[k]).shape for k in FIELDS}
 for row in vehicle.rows:
  assert all(np.asarray(row[k]).shape==expected[k]for k in FIELDS),'ACTUAL_PREFIX_STATE_SHAPE_CHANGED'
 arrays={k:np.concatenate([np.asarray(initial[k])[None],np.asarray([row[k]for row in vehicle.rows])],axis=0)if n else np.asarray(initial[k])[None]for k in FIELDS}
 arrays['applied_ctrl']=np.asarray([row['ctrl']for row in vehicle.rows])if n else np.empty((0,len(vehicle.d.ctrl)))
 assert all(np.isfinite(value).all()for value in arrays.values())
 target=output/'FULL_STATE_NPLUS1.npz';quota.save_npz(target,arrays,np)
 with np.load(target,allow_pickle=False)as stream:assert all(np.array_equal(stream[k],value)for k,value in arrays.items())
 return dict(recorded_actions=n,recorded_Nplus1_states=n+1,reported_actual_count=vehicle.count,unrecorded_actual_gap=vehicle.count-n,complete=vehicle.count==n,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),no_future_states_or_contacts_fabricated=True)
