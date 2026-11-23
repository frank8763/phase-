"""One future CPU2 original SCCR core query; no environment or physical step."""
import copy,math,os,time
from binding import bind,NoPlant
from context import C,O,R,read,sha

def run(payload,source):
 assert os.sched_getaffinity(0)=={2},'SCCR_QUERY_CPU2_ONLY'
 admission=read(O/'CURRENT_QUERY_ADMISSION.json');assert admission['query_authorized']and admission['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json'),'SCCR_QUERY_NOT_ADMITTED'
 assert payload['causal_point_map_adaptation']and payload['physical_admission']is False
 import numpy as np
 core,helpers,proof=bind(np,source);env=NoPlant(helpers,payload['known'],payload['config'],np)
 original=np.asarray(payload['original'],dtype=np.float32);points=np.asarray(payload['sensor_world_points'],dtype=np.float32).reshape(-1,2);body=payload['observation']['body']
 if not len(points):return dict(query_called=False,passed=False,reason='NO_CURRENT_CAUSAL_POINTS',models=0,physical_native=0,whole_navigation=False)
 nearest=int(np.argmin(np.linalg.norm(original-np.asarray(body[:2],np.float32),axis=1)));future=original[nearest:]
 if len(future)<3:return dict(query_called=False,passed=False,reason='FUTURE_ROUTE_TOO_SHORT',models=0,physical_native=0,whole_navigation=False)
 dx=points[:,0]-body[0];dy=points[:,1]-body[1];local_forward=math.cos(body[2])*dx+math.sin(body[2])*dy
 distance=env._phase21_point_segment_distances(points,future);mask=(local_forward>.05)&(local_forward<=payload['config']['phase21_path_lookahead']+.50)&(distance<payload['config']['phase21_corridor_radius']+payload['config']['phase21_v3_conflict_margin'])
 if not np.any(mask):return dict(query_called=False,passed=False,reason='NO_CURRENT_ROUTE_CONFLICT',models=0,physical_native=0,whole_navigation=False)
 conflict=points[mask];center=np.median(conflict,axis=0).astype(np.float32);index=int(np.argmin(np.linalg.norm(original-center,axis=1)));tangent=original[min(len(original)-1,index+2)]-original[max(0,index-2)];norm=float(np.linalg.norm(tangent))
 if norm<=1e-6:return dict(query_called=False,passed=False,reason='INVALID_PATH_TANGENT',models=0,physical_native=0,whole_navigation=False)
 normal=np.asarray([-tangent[1],tangent[0]],np.float32)/norm;offset=float(np.dot(center-original[index],normal));assert abs(offset)>.03,'SCCR_LATERAL_TIE_REQUIRES_ORIGINAL_SECTOR_BINDING'
 preferred=-1. if offset>.03 else 1.
 start=time.monotonic();candidate,count=core.search_continuous_corridor(env,original,points,conflict,center,index,preferred)
 return dict(query_called=True,query_attempts=1,query_returns=1,candidate_count=count,candidate_found=candidate is not None,selected_path=None if candidate is None else candidate.active_path.tolist(),original_core_used=True,helper_identity=proof,wall_s=time.monotonic()-start,physical_admission=False,whole_navigation=False,models=0,physical_native=0,original_SAC_and_full_fallback_stack_used=False,scope='explicit standalone SCCR geometric-core point-map adaptation only')
