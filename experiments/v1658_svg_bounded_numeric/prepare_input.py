"""One zero-integration public-map input from exactly recovered saved t0."""
import hashlib,json,math,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1658_svg_bounded_numeric'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def put(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n');t.replace(p)
def main():
 os.sched_setaffinity(0,{4});O.mkdir(exist_ok=True)
 with(O/'PREPARE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 recovery=R/'runs/v1641_original_evidence_pilot_recovery'
 assert read(recovery/'FULL_REMOTE_VERIFIED.json')['passed']
 members={x['path']:x for x in read(recovery/'ARCHIVE_INDEX.json')['files']}
 root=R/'runs/v1639_original_evidence_stages/pilot_WE_full'
 packet_path=root/'CANONICAL_INITIAL_PACKET.json';setup_path=root/'physics/SETUP.json'
 for p in [packet_path,setup_path]:assert members[str(p.relative_to(R))]['sha256']==sha(p)
 packet=read(packet_path);setup=read(setup_path)
 assert packet['native_tick']==0 and packet['sim_time']==0 and packet['body'][3:]==[0.,0.]
 assert packet['steering']['position']==packet['steering']['velocity']==[0.,0.]
 assert packet['controller_memory']==dict(last_ctrl=[0.,0.,0.,0.],integral=0.)
 assert not packet['steering_motion_active']and not packet['coupled_episode']
 known=setup['known'];rectangles=known['known_rectangles'];circles=known['known_circles']
 def occupied(x,y):
  return any(abs(x-cx)<=hx and abs(y-cy)<=hy for cx,cy,hx,hy in rectangles)or any(math.hypot(x-cx,y-cy)<=radius for cx,cy,radius in circles)
 n=100;resolution=.1;collision=[];distance=[];angle=[];speed=[]
 for ix in range(n):
  x=5.-(ix+.5)*resolution
  for iy in range(n):
   y=5.-(iy+.5)*resolution
   collision.append(float(occupied(x,y)));distance.append(abs(y-setup['case']['goal_xy'][1]));angle.append(0.);speed.append(.1)
 maps=dict(nx=n,ny=n,resolution=resolution,center=[0.,0.],index_orientation='grid_map native descending x/y; flat index=ix*ny+iy',collision_layer=collision,distance_field=distance,angle_field=angle,speed_field=speed,point_occupancy_only_not_footprint_certificate=True)
 put(O/'MAPS.json',maps)
 config=dict(qualification_only=True,not_benchmark_parameters=True,author_vehicle_not_Phase_plant=True,parameters=[.05,.1,.45,-.45,5.,-3.,.135,.189,.025,.1,1.,.01,1.,1.,.01,3.,.1,.1,.01,3.,.01,.005,.1,.001,.1],integers=[15,32,1,8,2,1,1],thread_count=1,outer_constructor_limit=1,solve_limit=1,internal_kinematic_rollout_steps=None)
 put(O/'CONFIG.json',config)
 inp=dict(scope='SAVED_EXPOSED_STATIC_T0_AUTHOR_CORE_MATH_ONLY',models_authorized=False,physical_admission=False,source_packet_path=str(packet_path.relative_to(R)),source_packet_sha256=sha(packet_path),source_setup_path=str(setup_path.relative_to(R)),source_setup_sha256=sha(setup_path),remote_input_index_sha256=sha(recovery/'ARCHIVE_INDEX.json'),original_packet=packet,state=[*packet['body'][:4],0.],steering_mapping='only exact measured neutral-wheel0; no general conversion claim',public_goal=setup['case']['goal_xy'],public_known_geometry=dict(known_rectangles=rectangles,known_circles=circles),maps_sha256=sha(O/'MAPS.json'),config_sha256=sha(O/'CONFIG.json'),actor_truth_or_phase_supplied=False,historical_controls_supplied=False,reference_not_certified_route=True)
 put(O/'INPUT.json',inp)
 put(O/'PREPARATION_CHECKPOINT.json',dict(unix=time.time(),status='INPUT_PREPARED_NUMERIC_OWNER_SOURCE_FREEZE_RECOVERY_ADMISSION_STILL_REQUIRED',input_sha256=sha(O/'INPUT.json'),maps_sha256=sha(O/'MAPS.json'),config_sha256=sha(O/'CONFIG.json'),models=0,FFI_loads=0,optimizer_calls=0,physical_native=0,replay_native=0))
 print(json.dumps(dict(input_prepared=True,maps_cells=n*n,models=0,physical_admission=False)))
if __name__=='__main__':main()
