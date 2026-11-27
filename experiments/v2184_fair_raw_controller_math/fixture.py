"""One historical causal input and new common nominal window, no sensor fiction."""
import ast,copy,hashlib,json,math
from pathlib import Path
from context import R,read,sha
RECEIPT='runs/v1978_rpp_first_common_round/actual/cycle_0000_origin.json'
NOMINAL='runs/v2182_fairness_mechanism_diagnosis/NOMINAL_FRONTEND_GEOMETRY.json'
KNOWN='experiments/v855_renewal_worker/KNOWN_FIELD.json'
GRID='experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json'
PARAMS='experiments/v1370_overnight_controller_matrix/rpp_default_params.json'
OBS='experiments/v1922_dwa_five_admission_checked/observation.py'
CLOCK='experiments/v1694_shared_observation_closure/contract.py'
TWIST='experiments/v1288_baseline_interface/contract.py'
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def functions(path,names,env):
    nodes=[copy.deepcopy(n)for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names]
    assert {n.name for n in nodes}==set(names);scope=dict(env)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope);return scope
def build(source):
    for n in [RECEIPT,NOMINAL,KNOWN,GRID,PARAMS,OBS,CLOCK,TWIST]:assert source[n]==sha(R/n),'MATH_INPUT_SOURCE_CHANGED:'+n
    receipt=read(R/RECEIPT)['receipt'];before=copy.deepcopy(receipt);p=receipt['packet'];assert p['native_tick']==0 and p['sim_time']==0.
    shared=functions(R/CLOCK,['native_clock','scan_only'],dict(copy=copy,math=math,NATIVE_DT=.01,CLOCK_TOLERANCE=1e-8,SCAN_KEYS=('native_tick','time','xy','yaw','ranges')))
    verify=functions(R/OBS,['verify'],dict(copy=copy,math=math,digest=digest,scan_only=shared['scan_only']))['verify'];verify(receipt,0,0.)
    nominal=read(R/NOMINAL);assert nominal['passed']and nominal['public_static_only']and nominal['hidden_actor_truth_used']is False
    path=copy.deepcopy(nominal['common_first_local_window']);assert len(path)>=2 and nominal['local_window_report']['arc_length_m']==.6
    gear=nominal['local_window_report']['gear'];assert gear==1
    known=read(R/KNOWN);known={k:known[k]for k in ['known_rectangles','known_circles']}
    body=copy.deepcopy(p['body']);rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),*body[2:]]
    common=dict(schema='V2184_FIXED_SAVED_CAUSAL_RAW_CONTROLLER_MATH_V1',native_tick=0,sim_time=0.,body=body,rear_body=rear,steering=copy.deepcopy(p['steering']),controller_memory=copy.deepcopy(p['controller_memory']),scan=copy.deepcopy(receipt['scan']),local_rear_path=path,gear=gear,actual_global_goal_xy=nominal['report']['actual_whole_goal_xy'],public_geometry_sha256=sha(R/KNOWN),public_grid_sha256=sha(R/GRID),source_packet_sha256=receipt['packet_sha256'],historical_timestamps_preserved=True,actual_current_observation_or_physical_authority=False)
    assert receipt==before
    return common,known
def strict_domain(v,w,gear,source):
    assert source[TWIST]==sha(R/TWIST)
    f=functions(R/TWIST,['number','twist'],dict(math=math,SPEED=.1,CURVATURE=1/1.32))['twist']
    a,b=f(v,w);assert abs(a)<.005 or a*gear>0,'RAW_OUTPUT_GEAR_REFUSED'
    return [a,b,False]
