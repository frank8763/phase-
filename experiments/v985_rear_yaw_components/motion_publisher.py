"""Resume causal sensor/filter history only, then exact frozen V977 publisher."""
import copy,importlib.util,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v979_original_causal_publisher',R/'experiments/v968_rpp_closed_loop_night/motion_publisher.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def seed_history(instance,seed):
    rows=seed['states'];assert rows and rows[-1]['native_tick']==seed['source']['source_native_tick']
    assert all(row['native_tick']<=seed['source']['source_native_tick']for row in rows)
    instance.tracker.rows=copy.deepcopy(rows);instance.tracker.latest=copy.deepcopy(rows[-1]);instance.tracker.when=rows[-1]['time']
    instance.tracker.support=np.asarray(rows[-1]['support_bounds'],float);instance.tracker.last_hit=rows[-1]['last_hit_time']
    instance.observations=copy.deepcopy(seed['observations']);instance.known_packets=len(instance.observations)
    instance.scan_monotonic=time.monotonic()
    for row in rows:instance.periodic.update(row['time'],row['native_tick'],row['support_bounds'])
    actual=instance.periodic.snapshot();expected=seed['source']['periodic']
    assert all(actual[k]==expected[k]for k in ['omega','amplitude','last','source_tick'])
    assert all(np.asarray(a).shape==np.asarray(b).shape and np.allclose(a,b,rtol=0,atol=1e-9)for a,b in zip(actual['vertices'],expected['vertices'])),'CAUSAL_PERIODIC_RESTORE_MISMATCH'
    return dict(passed=True,restored_causal_rows=len(rows),source_tick=actual['source_tick'],models=0,integrations=0)

class MotionPublisher(base.MotionPublisher):
    def __init__(self,node,out):
        super().__init__(node,out)
        task=json.loads((Path(out)/'TASK.json').read_text())
        if not task.get('origin_native_tick',0):return
        seed=json.loads((R/task['seed_history']).read_text())
        with self.lock:proof=seed_history(self,seed)
        (Path(out)/'CAUSAL_HISTORY_RESTORE.json').write_text(json.dumps(proof,indent=2)+'\n')
