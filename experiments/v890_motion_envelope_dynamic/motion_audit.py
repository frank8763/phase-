"""Independent saved observation/map reconstruction; no simulator loading."""
import gzip,hashlib,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v889_motion_envelope_software'),str(R/'experiments/v887_exact_lidar_software')]
from envelope import Envelope,raster,HORIZON,MAP_LATENCY_RESERVE
from exact_lidar import get_lidar_features
def audit(out):
    out=Path(out);journal=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()));setup=json.loads((out/'physics/SETUP.json').read_text());sensors=json.loads(gzip.decompress((out/'physics/SENSORS.json.gz').read_bytes()));catalog={p['native_tick']:{k:p[k]for k in ['native_tick','time','xy','yaw','ranges']}for p in sensors};tracker=Envelope(setup['known'],get_lidar_features);states={};covered=0
    assert len(journal['observations'])==len(journal['states'])
    for packet,expected in zip(journal['observations'],journal['states']):
        assert packet==catalog[packet['native_tick']],'ONLINE_SCAN_NOT_ORIGINAL_MEASUREMENT'
        actual=tracker.update(packet)
        for key in actual:
            if key in ['position_lower','position_upper']and actual[key]is not None:
                assert np.allclose(actual[key],expected[key],rtol=0,atol=1e-10),'CAUSAL_ENCLOSURE_RECONSTRUCTION_CHANGED'
            else:assert actual[key]==expected[key],'CAUSAL_ENCLOSURE_METADATA_CHANGED'
        states[packet['native_tick']]=expected
        if actual['information_mode']=='TRACKED':
            c=setup['actor'];xy=np.asarray(c['anchor_xy'])+np.asarray(c['axis_xy'])*c['amplitude_m']*math.sin(c['omega_rad_s']*packet['time']+c['phase_rad'])
            assert np.all(xy>=np.asarray(actual['position_lower'])-1e-8)and np.all(xy<=np.asarray(actual['position_upper'])+1e-8),'OFFLINE_ACTOR_OUTSIDE_CAUSAL_ENCLOSURE';covered+=1
    tracked_publications=0
    for publication in journal['publications']:
        state=states[publication['source_native_tick']];assert state['time']==publication['source_scan_sim_time']
        age=publication['forecast_sim_time']-state['time'];pad=.1+.08*(max(0.,age)+HORIZON+MAP_LATENCY_RESERVE)
        expected=None if state['position_lower']is None else [*(np.asarray(state['position_lower'])-pad),*(np.asarray(state['position_upper'])+pad)]
        assert (expected is None and publication['rectangle']is None)or(expected is not None and np.allclose(expected,publication['rectangle'],rtol=0,atol=1e-10)),'PUBLISHED_FORECAST_NOT_CAUSAL_STATE'
        payload=raster(publication['rectangle']).tobytes();assert hashlib.sha256(payload).hexdigest()==publication['map_sha256'],'FORECAST_MAP_SHA_CHANGED'
        if expected is not None:tracked_publications+=1
    snapshots=json.loads((out/'COSTMAP_SNAPSHOT_INDEX.json').read_text());snapshot_types=set()
    for row in snapshots:
        assert abs(row['resolution']-.01)<1e-8
        with np.load(out/row['path'])as z:assert len(z['data'])==row['width']*row['height']
        snapshot_types.add(row['kind'])
    result=dict(passed=not journal['truth_used']and covered>0 and tracked_publications>0 and snapshot_types=={'local_costmap','global_costmap'},original_observations_verified=len(journal['observations']),tracked_states_with_offline_true_center_covered=covered,forecast_publications_rebuilt=len(journal['publications']),tracked_forecast_publications=tracked_publications,actual_costmap_snapshot_kinds=sorted(snapshot_types),models=0,integrations=0,scope='Causal dataflow/finite enclosure and actual map snapshots only; physical navigation and recursive safety separate')
    (out/'MOTION_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
