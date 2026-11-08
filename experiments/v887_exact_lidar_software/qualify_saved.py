"""Run the genuine Vehicle.scan method on saved inputs, without importing a model."""
import ast,copy,gzip,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v887_exact_lidar_software';REC=R/'records/nav2_v887_20261108'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=True);REC.mkdir(exist_ok=True)
    source=R/'experiments/v858_nav2_verified/vehicle.py'
    original=load('original_sampled_lidar',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py')
    sys.modules['phase14_sensor_utils']=original
    noise=load('original_sensor_noise',R/'experiments/v733_early_low_translation_scan/sensor_model.py')
    fast=load('new_exact_sampled_lidar',C/'exact_lidar.py')
    node=next(x for x in ast.parse(source.read_text()).body if isinstance(x,ast.ClassDef)and x.name=='Vehicle')
    method=next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name=='scan')
    base=R/'runs/v858_nav2_verified/v886/main_we/physics';setup=json.loads((base/'SETUP.json').read_text());config=setup['actor']
    saved=json.loads(gzip.decompress((base/'SENSORS.json.gz').read_bytes()))
    def actor_xy(t):return np.asarray(config['anchor_xy'])+np.asarray(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*t+config['phase_rad'])
    def function(lidar):
        env=dict(np=np,SimpleNamespace=SimpleNamespace,corrupt=noise.corrupt,get_lidar_features=lidar)
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),env)
        return env['scan']
    def vehicle():return SimpleNamespace(known=setup['known'],seed=setup['seed'],noise=setup['noise'],actor=SimpleNamespace(xy=actor_xy),first_detection=None,sensor_rows=[])
    def batch(lidar,rows):
        scan=function(lidar);v=vehicle();elapsed=[];packets=[];cpu=time.thread_time();wall=time.perf_counter()
        for row in rows:
            x,y=row['xy'];yaw=row['yaw'];v.body=lambda:(x,y,yaw,0.,0.);v.d=SimpleNamespace(time=row['time']);v.count=row['native_tick']
            begun=time.perf_counter();packets.append(scan(v));elapsed.append(time.perf_counter()-begun)
        return packets,v.first_detection,dict(wall_s=time.perf_counter()-wall,thread_cpu_s=time.thread_time()-cpu,p50_s=float(np.median(elapsed)),p95_s=float(np.quantile(elapsed,.95)),maximum_s=max(elapsed))
    if sys.argv[1:]==['--baseline-only']:
        _,_,timing=batch(original.get_lidar_features,saved[:16])
        data=dict(expected_red_baseline=True,passed=timing['p95_s']<=.005,software_only_scan_p95_budget_s=.005,timing=timing,models=0,integrations=0)
        (O/'BASELINE_RED.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data));return 0 if data['passed']else 1
    old,old_detection,old_timing=batch(original.get_lidar_features,saved)
    new,new_detection,new_timing=batch(fast.get_lidar_features,saved)
    checks=dict(all260_original_saved_packets_exact=old==saved,all260_new_packets_exact_original=new==old,first_detection_exact=new_detection==old_detection,saved_prefix_really_has_no_detection=old_detection is None,software_component_scan_p95_below5ms=new_timing['p95_s']<=.005)
    # Predeclared software poses, not navigation outcomes, exercise visible actor returns.
    fixtures=[]
    for i,t in enumerate([0.,1.,2.,3.,4.,5.,6.,7.]):
        xy=actor_xy(t)-[1.,0.]
        fixtures.append(dict(native_tick=5*i+5,time=t,xy=xy.tolist(),yaw=0.))
    a,ad,_=batch(original.get_lidar_features,fixtures);b,bd,_=batch(fast.get_lidar_features,fixtures)
    checks['synthetic_positive_actor_attribution_exact']=a==b and ad==bd and ad is not None
    boundary_cases=0
    for location in [[-5.,0.],[5.,0.],[0.,-5.],[0.,5.],[0.,0.],[.08,0.],[-.08,0.]]:
        for angle in [0.,math.pi/2,math.pi,math.pi*3/2]:
            env=SimpleNamespace(robot_xy=np.asarray(location,np.float32),robot_yaw=angle,map_min=-5.,map_max=5.,rect_obstacles=np.asarray([[.16,0.,.08,.08]],np.float32),circle_obstacles=np.asarray([[0.,.16,.08],[.08,0.,0.]],np.float32))
            expected=original.get_lidar_features(env,32,3.);actual=fast.get_lidar_features(env,32,3.)
            assert np.array_equal(actual,expected),(location,angle);boundary_cases+=1
    checks['all28_fixed_boundary_frames_bitwise_exact']=boundary_cases==28
    result=dict(passed=all(checks.values()),checks=checks,models=0,environment_initializations=0,native_integrations=0,navigation_attempts=0,real_ros_servers=0,saved_frames=len(saved),synthetic_positive_frames=8,synthetic_boundary_frames=boundary_cases,original_component_timing=old_timing,new_component_timing=new_timing,component_wall_speed_ratio=old_timing['wall_s']/new_timing['wall_s'],component_thread_cpu_speed_ratio=old_timing['thread_cpu_s']/new_timing['thread_cpu_s'],original_scan_source_sha256=sha(source),new_lidar_source_sha256=sha(C/'exact_lidar.py'),model_window_started=False,limitations=['Source-exact genuine scan method with saved body/actor inputs; no new physical rollout','5ms is a software preparation target, not a replacement for original100ms gate','No proof of repaired physical timing or dynamic arrival','New physical integration requires a separate bounded protocol; V886 not restarted'])
    for p in [O/'QUALIFICATION.json',REC/'QUALIFICATION.json']:p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
