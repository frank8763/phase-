"""Recompute frozen raw ray cast and seeded corruption, with zero integration."""
import ast,hashlib,importlib.util,json,math
from pathlib import Path
from types import SimpleNamespace
import numpy as np

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v702_rpccr_prospective_compute'
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
records=read(root/'prospective01/PREFLIGHTS.json');tasks=read(Path(__file__).parent/'TASK_LIST.json');assert [x['task'] for x in records]==tasks;details=[]
for record in records:
    task=record['task'];pair=repo/record['run'];packet=read(pair/'INITIAL_UNSEEN.json')['packet'];config=read(pair/'DYNAMIC_PROTOCOL.json');provenance=read(pair/'INITIALIZATION_PROVENANCE.json')
    center=np.asarray(config['anchor_xy'])+np.sin(config['phase_rad'])*config['amplitude_m']*np.asarray(config['axis_xy'])
    env=SimpleNamespace(robot_xy=np.asarray(packet['xy'],np.float32),robot_yaw=packet['yaw'],map_min=-5.,map_max=5.,rect_obstacles=np.empty((0,4),np.float32),circle_obstacles=np.asarray([[*center,config['radius_m']]],np.float32))
    errors={}
    for tag in ['lidar','depth']:
        maximum=packet[tag+'_max_range'];n=len(packet[tag]);idx=provenance['noise_call_state_after_bootstrap'][tag+'_call']
        if tag=='lidar':raw=sensor.get_lidar_features(env,num_rays=n,max_range=maximum)
        else:
            half=math.radians(70.)*.5
            raw=np.asarray([sensor.ray_cast_distance(env,float(env.robot_yaw)-half+2.*half*i/(n-1),max_range=maximum,step=.08)/maximum for i in range(n)],np.float32)
        expected=corrupt(raw,task['seed'],idx,tag,maximum)
        errors[tag]=float(np.max(abs(expected-np.asarray(packet[tag]))))
    details.append({'slot':task['slot'],'task_seed':task['seed'],'maximum_packet_errors':errors,'passed':max(errors.values())==0. and provenance['task_noise_seed']==task['seed'] and provenance['bootstrap_seed']==95000011 and provenance['initial_time']==0. and read(pair/'INITIAL_UNSEEN.json')['passed'] and read(pair/'v699_preflight/INITIAL_UNSEEN_AUDIT_V699.json')['status']=='PASS' and read(pair/'TASK_FEASIBILITY.json')['eligible'] and config['phase_rad']==task['phase'] and config['swept_envelope_reference']['eligible'] and config['protected_junction_clearance_of_sweep_m']>=.05 and sha(pair/'scene_model.mjb')==sha(repo/'runs/v695_discovery_verified_fixture/phase0/paired/scene_model.mjb') and np.array_equal(read(pair/'STATIC_PROTOCOL.json')['start_qpos'],read(repo/'runs/v695_discovery_verified_fixture/phase0/paired/STATIC_PROTOCOL.json')['start_qpos'])})
result={'status':'PASS' if len(details)==4 and all(x['passed'] for x in details) else 'FAIL','tasks':len(details),'details':details,'frozen_sensor_constants':constants,'source_sha256':{'corruption':sha(source),'raycast':sha(sensor_source),'this_auditor':sha(Path(__file__))},'simulation_steps':0,'scope':'Exact t0 packets confirm original per-task noise keys and frozen corruption parameters after fixed bootstrap; no navigation or general stochastic coverage claim.'}
(root/'PREFLIGHT_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'bad_slots':[x for x in details if not x['passed']],'tasks':len(details),'parameters':constants}));assert result['status']=='PASS'
