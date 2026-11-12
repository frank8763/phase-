"""Exact 186-feature legacy layout. Missing modalities are errors, never padding."""
import numpy as np
BLOCKS={'phase5_base':66,'lidar':32,'camera_goal':5,'safety':4,'phase7_depth':15,'phase7_depth_summary':5,'outer_lidar':32,'outer_camera_goal':5,'outer_depth':15,'outer_depth_summary':5}
def assemble(blocks,base_actor,native_tick,measurement_native_tick):
 assert native_tick==measurement_native_tick,'STALE_POLICY_OBSERVATION'
 assert set(blocks)==set(BLOCKS),'EXACT_MEASURED_MODALITIES_REQUIRED'
 a={}
 for key,size in BLOCKS.items():
  a[key]=np.asarray(blocks[key],dtype=np.float32);assert a[key].shape==(size,)and np.isfinite(a[key]).all(),'INVALID_FEATURE_BLOCK '+key
 phase6=np.concatenate([a['phase5_base'],a['lidar'],a['camera_goal'],a['safety']]);assert phase6.shape==(107,)
 base=base_actor.predict(phase6);obs=np.concatenate([phase6,a['phase7_depth'],a['phase7_depth_summary'],base,a['outer_lidar'],a['outer_camera_goal'],a['outer_depth'],a['outer_depth_summary']]);assert obs.shape==(186,)
 return obs
