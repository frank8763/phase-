"""Red-capable actual-cache seam and actual saved frame/command tamper checks."""
import ast
import copy
import gzip
import importlib.abc
import sys
from types import SimpleNamespace
from component_context import *
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('QUALIFICATION_MODEL_IMPORT '+name)
sys.meta_path.insert(0,NoModel())
from frames import SampleCache,wire_packet,validate_wire,validate_binding,validate_frame
from fault_peer import command
from stamped_contract import assess_delivery

def main():
    task=read(C/'TASKS.json')[0];prior=Path(task['prior_raw']);journal=read(prior/'APPLIED_JOURNAL.json')
    with gzip.open(prior/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    saved=next(s for s in sensors if s['native_tick']==41390)
    assert validate_frame(saved,41390,413.9,journal[41390]['body'])
    clock=[10.];calls=[]
    class MetadataCursor:
        count=41390;d=SimpleNamespace(time=413.9)
        def body(self):return journal[self.count]['body']
        def scan(self):
            calls.append(self.count)
            return dict(native_tick=self.count,time=self.d.time,xy=self.body()[:2],yaw=self.body()[2],ranges=saved['ranges'])
    # Metadata cursor deliberately has no model or integration; synthetic later
    # ranges are never passed off as absent historical 41410 sensor evidence.
    cursor=MetadataCursor();cache=SampleCache(lambda:clock[0]);wires=[]
    pattern=read(R/'runs/v1371_overnight_retrospective/REPRODUCTION.json')['metadata_cache_pattern']
    tree=ast.parse((R/'experiments/v1370_overnight_controller_matrix/route_native.py').read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='scan is None or now - scan_at >= 0.04')
    code=compile(ast.Module(body=[node],type_ignores=[]),'<original-production-condition>','exec')
    namespace=dict(v=cursor,scan=None,scan_at=0.)
    for index,e in enumerate(pattern):
        cursor.count=e['packet_native'];cursor.d.time=cursor.count*.01;clock[0]=10.+e['wall_offset']
        namespace['now']=clock[0];exec(code,namespace)
        wires.append(wire_packet(cache,cursor,task['run_id'],index));assert wires[-1]['native_tick']==wires[-1]['sensor_frame']['native_tick']
    assert namespace['scan']['native_tick']==41390 and wires[-1]['native_tick']==41410,'RED_PATTERN_NOT_REPRODUCED'
    at=wires[-1]['sampled_at'];clock[0]+=.001
    same=wire_packet(cache,cursor,task['run_id'],len(wires));assert same['sampled_at']==at
    clock[0]=at+.041;refreshed=wire_packet(cache,cursor,task['run_id'],len(wires)+1);assert refreshed['sampled_at']==clock[0]
    rejects=[]
    def reject(name,fn):
        try:fn()
        except (AssertionError,KeyError,ValueError):rejects.append(name)
        else:raise AssertionError('BAD_INPUT_ACCEPTED '+name)
    for field,value in [('native_tick',41390),('time',413.9),('xy',[0.,0.]),('yaw',0.),('sampled_at',0.)]:
        bad=copy.deepcopy(wires[-1]);bad['sensor_frame'][field]=value
        reject('sensor_'+field,lambda b=bad:validate_wire(b))
    wire=wires[-1];sent={wire['sequence']:wire};packet=command(wire,0,clock[0]);validate_binding(packet,sent)
    for field,value in [('observation_native_tick',41390),('observation_sampled_at',clock[0]),('observation_sequence',999),('run_id','foreign')]:
        bad=dict(packet);bad[field]=value;reject('command_'+field,lambda b=bad:validate_binding(b,sent))
    stale=command(wire,1,wire['sampled_at']+.21)
    assert assess_delivery(stale,wire['sampled_at']+.211,run_id=task['run_id'],previous_sequence=0)['reason']=='OBSERVATION_EXPIRED'
    fresh=command(refreshed,2,refreshed['sampled_at']+.001)
    assert assess_delivery(fresh,refreshed['sampled_at']+.002,run_id=task['run_id'],previous_sequence=1)['accepted']
    # Repeated/future command and missing authority are fail-closed.
    reject('replayed_command',lambda:assess_delivery(fresh,refreshed['sampled_at']+.002,run_id=task['run_id'],previous_sequence=2))
    reject('unauthorized_models',lambda:authorize(task,{}))
    assert sources()
    dump(O/'QUALIFICATION.json',dict(passed=True,old_actual_AST_cache_red=True,new_production_cache_green=True,saved_actual_frame_positive=True,
        rejected=rejects,metadata_cursor_not_physics=True,missing_old_scan_never_fabricated=True,models=0,physical_native=0,replay_native=0,
        tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
    print(json.dumps(dict(passed=True,negative_cases=len(rejects),models=0,physical_native=0)))
if __name__=='__main__':main()
