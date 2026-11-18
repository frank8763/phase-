"""Correctness gates at the actual prefix/preview/composition boundary."""
from pathlib import Path
import copy
import json
import time
from refuge_onward import R, q, np, synthesize
from preview_search import search, PreviewGeometry
from connection import endpoint

C = Path(__file__).resolve().parent
O = R/'runs/v1201_refuge_onward_connection'


def read_case(version, task):
    root = R/'runs/v858_nav2_verified'/version/task
    x = json.loads((root/'LIVE_GOAL_INPUT.json').read_text())
    with np.load(root/'LIVE_GOAL_TABLE.npz') as z:
        table = {key:z[key].copy() for key in z.files}
    return root, x, table


def qualify():
    _, x, table = read_case('v1195', 'recovery_main_slot01')
    source_before = copy.deepcopy(x['source'])
    packet_before = copy.deepcopy(x['packet'])
    smoke = synthesize(x, table, time.monotonic()-1)
    assert not smoke['passed'] and smoke['analytical_cpp_native'] == 0
    q.dump(O/'ENTRY_SMOKE.json', smoke)
    assert not json.loads((O/'ENTRY_SMOKE.json').read_text())['passed']
    engine = q.accelerator.Engine(x['setup'], q.model.parameters()['coefficients'])
    origin = dict(q.initial(x['packet']), steering_load_episode=False)
    prefix = [(-.16,.12,200,0),(0.,0.,2200,0)]
    ps,pu,pm = engine.simulate(origin,prefix)
    predicted = endpoint(origin,ps,pm,True)
    suffix = [(.16,.12,100,0),(0.,0.,2200,0)]
    ts,tu,tm = engine.simulate(predicted,suffix)
    fs,fu,fm = engine.simulate(origin,prefix+suffix)
    k = len(pu)
    error = max(float(abs(fs[:k+1]-ps).max()),float(abs(fs[k:]-ts).max()),
                float(abs(fu[:k]-pu).max()),float(abs(fu[k:]-tu).max()),
                float(abs(fm[:k+1]-pm).max()),float(abs(fm[k:]-tm).max()))
    assert error <= 1e-8
    geometry = q.Geometry(x,table)
    shifted = PreviewGeometry(geometry,k)
    a,b = shifted.components(ts[:,:3],np.arange(len(ts)))
    ca,cb = geometry.components(ts[:,:3],np.arange(len(ts))+k)
    wrong_a,wrong_b = geometry.components(ts[:,:3],np.arange(len(ts)))
    assert np.array_equal(a,ca) and np.array_equal(b,cb)
    sensitivity = float(abs(b-wrong_b).max())
    assert sensitivity > 1e-6, 'TIME_TEST_MUST_DETECT_ZERO_OFFSET_BUG'
    preview = dict(origin=predicted,native_offset=k)
    no_work = search(x,table,time.monotonic()-1,preview=preview)
    assert no_work['nominal_preview'] and no_work['native_offset'] == k
    assert no_work['analytical_cpp_native'] == 0 and not no_work['physical_eligible']
    rejected = []
    bad = copy.deepcopy(x)
    bad['packet']['sim_time'] += .01
    try:
        search(bad,table,time.monotonic()-1)
    except AssertionError:
        rejected.append('packet_clock')
    bad_preview = copy.deepcopy(preview)
    bad_preview['native_offset'] = -1
    try:
        search(x,table,time.monotonic()-1,preview=bad_preview)
    except AssertionError:
        rejected.append('negative_offset')
    bad_preview = copy.deepcopy(preview)
    bad_preview['origin']['last_ctrl'][0] = float('nan')
    try:
        search(x,table,time.monotonic()-1,preview=bad_preview)
    except AssertionError:
        rejected.append('nonfinite_memory')
    assert rejected == ['packet_clock','negative_offset','nonfinite_memory']
    assert source_before == x['source'] and packet_before == x['packet']
    result = dict(passed=True,composition_error=error,
                  correct_absolute_offset=True,wrong_offset_sensitivity=sensitivity,
                  tamper_rejected=rejected,source_and_packet_not_rewritten=True,
                  actual_full_entry_zero_work=True,analytical_cpp_native=engine.native,
                  models=0,new_mujoco_native=0,physical_eligible=False)
    q.dump(O/'ENTRY_GATES.json',result)
    return result
