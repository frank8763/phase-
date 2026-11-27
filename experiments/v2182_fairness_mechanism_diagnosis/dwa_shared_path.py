"""New DWA module input preparation; native control functions are NOT executed."""
import ast,copy,hashlib,json,math
from pathlib import Path

R=Path(__file__).resolve().parents[2]
UP='runs/v1675_dwa_reference_intake/upstream/PathPlanning/DynamicWindowApproach/dynamic_window_approach.py'
OLD_CONFIG='runs/v1923_dwa_five_checked_queue/rounds/common_12__DWA/REFERENCE_CONFIG.json'
FUNCTIONS=['dwa_control','motion','calc_dynamic_window','predict_trajectory','calc_control_and_trajectory','calc_obstacle_cost','calc_to_goal_cost']
KAPPA=1/1.32
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def configuration(source):
    p=R/OLD_CONFIG;assert source[OLD_CONFIG]==sha(p)
    old=json.loads(p.read_bytes());assert old['max_accel']==.2 and old['dt']==.1 and old['v_resolution']==.01
    assert old['robot_length']==.88 and old['robot_width']==.75 and old['robot_stuck_flag_cons']==0.
    new=dict(old,max_speed=.1,min_speed=-.1,max_yaw_rate=.1*KAPPA,maximum_curvature=KAPPA,dt=.05,v_resolution=.005)
    changed={k:dict(before=old[k],after=new[k])for k in old if old[k]!=new[k]}
    assert set(changed)=={'max_speed','min_speed','max_yaw_rate','maximum_curvature','dt','v_resolution'}
    assert math.isclose(new['v_resolution'],new['max_accel']*new['dt']/2,rel_tol=0.,abs_tol=1e-15)
    return new,dict(declared_new_group_changes=changed,old_config_unchanged=True,query_executed=False)

def sample_allowed(v,w,gear):
    assert gear in(-1,1)and type(gear)is int
    assert type(v)in(int,float)and type(w)in(int,float)and math.isfinite(v)and math.isfinite(w)
    return v*gear>=.005 and abs(w)<=abs(v)*KAPPA+1e-12

def source_ast(source):
    path=R/UP;assert source[UP]==sha(path),'UPSTREAM_DWA_SOURCE_CHANGED'
    original=ast.parse(path.read_text());nodes=[];proof={}
    for name in ['RobotType',*FUNCTIONS]:
        old=next(n for n in original.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name==name)
        n=copy.deepcopy(old);old_dump=ast.dump(old,include_attributes=False)
        if name=='calc_control_and_trajectory':
            outer=next(n for n in n.body if isinstance(n,ast.For));inner=next(n for n in outer.body if isinstance(n,ast.For))
            assert ast.unparse(outer.iter)=='np.arange(dw[0], dw[1], config.v_resolution)'
            assert ast.unparse(inner.iter)=='np.arange(dw[2], dw[3], config.yaw_rate_resolution)'
            assert ast.unparse(inner.body[0])=='trajectory = predict_trajectory(x_init, v, y, config)'
            inner.body.insert(0,ast.parse('if not _phase_signed_gear_mask(float(v), float(y), _phase_segment_gear):\n continue').body[0])
            reverted=copy.deepcopy(n);a=next(n for n in reverted.body if isinstance(n,ast.For));b=next(n for n in a.body if isinstance(n,ast.For));b.body.pop(0)
            assert ast.dump(reverted,include_attributes=False)==old_dump
        else:assert ast.dump(n,include_attributes=False)==old_dump
        nodes.append(n);proof[name]=dict(upstream_AST_sha256=hashlib.sha256(old_dump.encode()).hexdigest(),new_AST_sha256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),only_signed_gear_mask_added=name=='calc_control_and_trajectory')
    return ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),proof

def frame_inputs(view,*,expected_view_sha256):
    assert digest(view)==expected_view_sha256 and view['schema']=='PHASE_SHARED_MODULE_CANDIDATE_V1'
    assert view['control_native']==5 and view['producer_execution_or_physical_safety_verified']is False
    assert view['route']['frame']=='REAR_AXLE_ODOM'
    body=view['body'];rear=view['rear_body'];assert len(body)==len(rear)==5
    assert all(type(v)in(int,float)and math.isfinite(v)for v in [*body,*rear,*view['actual_whole_goal_xy']])
    reconstructed=[rear[0]+.3*math.cos(rear[2]),rear[1]+.3*math.sin(rear[2]),*rear[2:]]
    assert max(abs(a-b)for a,b in zip(reconstructed,body))<=1e-12,'REAR_BODY_FRAME_INCONSISTENT'
    segment=view['segment'];assert type(segment['gear'])is int and segment['gear']in(-1,1)
    poses=segment['poses'];assert 2<=len(poses)<=10000
    converted=[]
    for p in poses:
        assert len(p)==4 and all(type(v)in(int,float)and math.isfinite(v)for v in p)
        converted.append([p[0]+.3*math.cos(p[2]),p[1]+.3*math.sin(p[2]),p[2],p[3]])
    return dict(input_view_sha256=expected_view_sha256,
        DWA=dict(state_body_center=copy.deepcopy(body),segment_body_poses=converted,planning_goal_xy=converted[-1][:2],segment_gear=segment['gear']),
        RPP=dict(state_rear_axle=copy.deepcopy(rear),segment_rear_poses=copy.deepcopy(poses),segment_gear=segment['gear']),
        actual_whole_goal_xy=copy.deepcopy(view['actual_whole_goal_xy']),
        planning_goal_is_not_arrival=True,original_full_response_tracking_and_stop_required=True,
        native_unicycle_to_controlled_plant_equivalence_proven=False,physical_launch_authorized=False)
