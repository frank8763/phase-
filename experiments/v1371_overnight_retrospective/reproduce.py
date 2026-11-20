"""Minimal recorded-evidence reproduction; no models or physical replay."""
import ast
import gzip
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1370/rpp_local_horizon_m1_s01_main'

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('NO_MODEL_REVIEW '+name)
sys.meta_path.insert(0,NoModel())

def read(p):return json.loads(p.read_text())
def main():
    begin=time.monotonic();tick=41410
    events=[e for e in read(RAW/'DYNAMIC_RESERVE_RECORDS.json') if e['native_tick']==tick]
    commands=[e for e in read(RAW/'ROS_COMMANDS.json') if e['sequence'] in {x['command_sequence'] for x in events}]
    forecasts=[e for e in read(RAW/'FORECAST_RECORDS.json') if e['native_tick']==tick]
    with gzip.open(RAW/'physics/SENSORS.json.gz','rt') as f:all_sensors=json.load(f)
    before=max((x for x in all_sensors if x['native_tick']<tick),key=lambda x:x['native_tick'])
    after=min((x for x in all_sensors if x['native_tick']>tick),key=lambda x:x['native_tick'])
    sensors=[before,after]
    source=R/'experiments/v1370_overnight_controller_matrix/dynamic_audit.py'
    spec=importlib.util.spec_from_file_location('frozen_original_dynamic_audit',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    try:module.review(events,commands,forecasts,sensors,forecast_kind='HORIZON')
    except KeyError as exc:assert exc.args==(tick,);error=repr(exc)
    else:raise AssertionError('SAVED_MISSING_SENSOR_SYMPTOM_NOT_REPRODUCED')
    # Execute the actual frozen cache refresh condition on an explicit metadata
    # clock/cursor. It cannot load or step a vehicle; count changes are fixture
    # metadata only, never reported as physical or replay integrations.
    native=ast.parse((R/'experiments/v1370_overnight_controller_matrix/route_native.py').read_text())
    condition=next(n for n in ast.walk(native) if isinstance(n,ast.If) and ast.unparse(n.test)=='scan is None or now - scan_at >= 0.04')
    code=compile(ast.Module(body=[condition],type_ignores=[]),'<actual-frozen-cache-condition>','exec')
    rejected=[e for e in read(RAW/'FRESHNESS_REJECTIONS.json') if before['native_tick']<=e['before_native']<tick]
    assert rejected and rejected[0]['before_native']==before['native_tick']
    origin=rejected[0]['decision']['receipt_monotonic'];observed=[]
    class Cursor:
        count=before['native_tick']
        def scan(self):return dict(sensor_native_tick=self.count)
    v=Cursor();namespace=dict(v=v,scan=None,scan_at=0.)
    for e in rejected:
        v.count=e['before_native'];namespace['now']=e['decision']['receipt_monotonic']-origin
        exec(code,namespace);observed.append(dict(packet_native=v.count,sensor_native=namespace['scan']['sensor_native_tick'],wall_offset=namespace['now']))
    v.count=tick;namespace['now']=rejected[-1]['decision']['receipt_monotonic']-origin+.001
    exec(code,namespace);observed.append(dict(packet_native=tick,sensor_native=namespace['scan']['sensor_native_tick'],wall_offset=namespace['now']))
    assert observed[-1]['sensor_native']==before['native_tick'] and observed[-1]['packet_native']==tick
    proof=dict(reproduced=True,original_audit_error=error,minimal_events=len(events),minimal_sensor_records=len(sensors),
        metadata_cache_pattern=observed,expiry_brake_native=sum(e['applied_native'] for e in rejected),
        previous_sensor_native=before['native_tick'],missing_sensor_native=tick,next_sensor_native=after['native_tick'],
        physical_native=0,models=0,replay_native=0,metadata_cursor_is_not_physics=True,wall_s=time.monotonic()-begin)
    (O/'REPRODUCTION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))

if __name__=='__main__':main()
