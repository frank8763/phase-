"""Closed-run original scan recomputation, without loading a vehicle model or ROS."""
import ast,fcntl,gzip,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v894_wait_map_validation';REC=R/'records/nav2_v894_20261108'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    completion=json.loads((O/'COMPLETION.json').read_text());assert completion['closed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    original=load('v894_closed_original_lidar',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py');sys.modules['phase14_sensor_utils']=original
    noise=load('v894_closed_original_noise',R/'experiments/v733_early_low_translation_scan/sensor_model.py')
    source=R/'experiments/v858_nav2_verified/vehicle.py';klass=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.ClassDef)and n.name=='Vehicle');method=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='scan')
    context=dict(np=np,SimpleNamespace=SimpleNamespace,get_lidar_features=original.get_lidar_features,corrupt=noise.corrupt)
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),context);scan=context['scan'];rows=[]
    for task in completion['rows']:
        root=Path(task['output']);p=root/'physics';setup=json.loads((p/'SETUP.json').read_text());native=json.loads((root/'RESULT.json').read_text());saved=json.loads(gzip.decompress((p/'SENSORS.json.gz').read_bytes()));config=setup['actor']
        def xy(t):return np.asarray(config['anchor_xy'])+np.asarray(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*t+config['phase_rad'])
        v=SimpleNamespace(known=setup['known'],seed=setup['seed'],noise=setup['noise'],actor=SimpleNamespace(xy=xy),first_detection=None,sensor_rows=[]);mismatches=[];begun=time.monotonic()
        for i,row in enumerate(saved):
            x,y=row['xy'];yaw=row['yaw'];v.body=lambda:(x,y,yaw,0.,0.);v.d=SimpleNamespace(time=row['time']);v.count=row['native_tick'];packet=scan(v)
            if packet!=row:mismatches.append(dict(index=i,native_tick=row['native_tick']))
            if i%200==0:(O/'SENSOR_READBACK_PROGRESS.json').write_text(json.dumps(dict(task_id=task['task_id'],checked=i+1,total=len(saved)))+'\n')
        first_matches=v.first_detection==native.get('first_actor_detection')
        rows.append(dict(task_id=task['task_id'],passed=not mismatches and first_matches,sensor_frames=len(saved),all_saved_ranges_raw_and_packet_fields_bitwise_exact_original=not mismatches,original_first_corrupted_actor_detection_exact=first_matches,mismatched_frames=mismatches,original_recomputed_first_detection=v.first_detection,wall_s=time.monotonic()-begun));print(json.dumps(rows[-1]),flush=True)
    result=dict(passed=bool(rows)and all(r['passed']for r in rows),rows=rows,models=0,environment_initializations=0,native_integrations=0,ros_servers=0,original_vehicle_scan_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Original genuine scan method recomputed on every closed actual scan; not new navigation or a new confirmation denominator')
    for p in [O/'FULL_SENSOR_EQUIVALENCE.json',REC/'FULL_SENSOR_EQUIVALENCE.json']:p.write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
