"""Recompute frozen raw ray cast and seeded corruption, with zero integration."""
import ast,hashlib,importlib.util,json,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v705_rpccr_prospective_pairs'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=repo/'runtime/home/mkmini_g11b_budget162_confirmatory_v1_1/g11b_budget162_confirmatory_v1.py'
names={'LIDAR_SIGMA_M','LIDAR_CLIP_M','LIDAR_DROPOUT','DEPTH_SIGMA_M','DEPTH_CLIP_M','DEPTH_DROPOUT'}
constants={}
for node in ast.parse(source.read_text()).body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id in names:constants[target.id]=ast.literal_eval(node.value)
assert set(constants)==names
sensor_source=repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py'
spec=importlib.util.spec_from_file_location('frozen_sensor_v697',sensor_source);sensor=importlib.util.module_from_spec(spec);spec.loader.exec_module(sensor)
def corrupt(raw,seed,idx,tag,maximum):
    raw=np.asarray(raw,dtype=np.float32);token=f'{seed}|{idx}|{tag}|{tuple(raw.shape)}'.encode()
    key=int.from_bytes(hashlib.sha256(token).digest()[:8],'little') & 0x7FFFFFFF
    rng=np.random.default_rng(key);prefix=tag.upper()
    noise=np.clip(rng.normal(0.,constants[prefix+'_SIGMA_M'],size=raw.shape),-constants[prefix+'_CLIP_M'],constants[prefix+'_CLIP_M']).astype(np.float32)
    dropout=rng.random(raw.shape)<constants[prefix+'_DROPOUT']
    shifted=np.clip(np.clip(raw,0.,1.)*maximum+noise,0.,maximum);shifted[dropout]=maximum
    return (shifted/maximum).astype(np.float32)
import sys
root=repo/'runs/v778_global_retained_reentry'
window=Path(sys.argv[1]);records=read(window/'PREFLIGHTS.json');tasks=read(Path(__file__).parent/'PILOT_TASKS.json');assert [x['task'] for x in records]==tasks
cases={x['id']:x for x in read(Path(__file__).parent/'SCENE_CASES.json')};known=read(Path(__file__).parent/'KNOWN_FIELD.json');details=[]
for record in records:
 task=record['task'];pair=repo/record['run'];initial=read(pair/'INITIAL_UNSEEN.json');packet=initial['packet'];config=read(pair/'DYNAMIC_PROTOCOL.json');provenance=read(pair/'INITIALIZATION_PROVENANCE.json');protocol=read(pair/'STATIC_PROTOCOL.json');arena=read(pair/'ARENA_CONSTRUCTION.json');case=cases[task['case_id']]
 center=np.asarray(config['anchor_xy'])+np.sin(config['phase_rad'])*config['amplitude_m']*np.asarray(config['axis_xy'])
 env=SimpleNamespace(robot_xy=np.asarray(packet['xy'],np.float32),robot_yaw=packet['yaw'],map_min=-5.,map_max=5.,rect_obstacles=np.asarray(protocol['known_rectangles'],np.float32).reshape(-1,4),circle_obstacles=np.asarray([*protocol['known_circles'],[*center,config['radius_m']]],np.float32).reshape(-1,3))
 errors={}
 for tag in ['lidar','depth']:
  maximum=packet[tag+'_max_range'];n=len(packet[tag]);idx=provenance['noise_call_state_after_bootstrap'][tag+'_call']
  if tag=='lidar':raw=sensor.get_lidar_features(env,num_rays=n,max_range=maximum)
  else:
   half=math.radians(70.)*.5;raw=np.asarray([sensor.ray_cast_distance(env,float(env.robot_yaw)-half+2.*half*i/(n-1),max_range=maximum,step=.08)/maximum for i in range(n)],np.float32)
  errors[tag]=float(np.max(abs(corrupt(raw,task['seed'],idx,tag,maximum)-np.asarray(packet[tag]))))
 gate=provenance.get('bootstrap_repair',{})
 checks={'raw_noise_exact':max(errors.values())==0.,'task_noise':provenance['task_noise_seed']==task['seed'],'fixed_bootstrap':provenance['bootstrap_seed']==95000011,'zero_time':provenance['initial_time']==0.,'all_initial_gates':initial['passed'] and all(initial['checks'].values()),'registered_start':protocol['start_qpos'][:2]==case['start_xy'],'registered_goal':np.array_equal(np.asarray(protocol['goal_xy'],np.float32),np.asarray(case['goal_xy'],np.float32)),'known_map':protocol['known_rectangles']==known['known_rectangles'] and protocol['known_circles']==known['known_circles'],'all19_known_geoms':len(arena['known_static_geometries_preserved'])==19 and not arena['removed_known_static_geometries'],'dynamic_phase':config['phase_rad']==task['phase'],'sweep_nonblocking':config['swept_envelope_reference']['eligible'] and config['protected_junction_clearance_of_sweep_m']>=.05 and config['known_obstacle_clearance_of_swept_envelope_m']>=.55,'actual_t0_feasible':read(pair/'TASK_FEASIBILITY.json')['eligible'],'early_reset_repair':gate.get('reset_calls')==1 and gate.get('disabled_before_original_reset') is True and gate.get('old_detour_calls')==gate.get('bootstrap_integrations')==0,'causal_audit':read(repo/record['causal_audit'])['status']=='PASS'}
 details.append({'slot':task['slot'],'case_id':task['case_id'],'passed':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()},'maximum_packet_errors':errors})
result={'status':'PASS' if len(details)==1 and all(x['passed'] for x in details) else 'FAIL','tasks':len(details),'details':details,'simulation_integrations':0,'scope':'One original WEST_EAST development task before navigation; no task rejection/replacement by navigation result'}
(window/'PREFLIGHT_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['status']=='PASS'
