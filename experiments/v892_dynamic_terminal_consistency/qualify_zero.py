"""Actual lazy-entry/adapter contracts with explicit fake vehicle; no model or ROS."""
import ast,hashlib,importlib.util,json,subprocess,sys,types
from pathlib import Path
from unittest.mock import patch
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v892_dynamic_terminal_consistency'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
import authority as a
from handshake import policy_packet
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checks={};tasks=read(C/'TASKS.json')
    old=read(R/'experiments/v881_timing_accounting_continuation/TASKS.json')
    original=next(t for t in old if t['variant']=='A'and t['case_id']=='WEST_EAST'and t['stage']=='dynamic_main')
    for t in tasks:
        checks[t['task_id']+'_unchanged_original_dynamic_course']=all(t[k]==original[k]for k in ['case_id','seed','phase','dynamic','goal_xy','goal_yaw','wall_limit_s','brake_s'])
    for n,h in read(R/'experiments/v888_exact_lidar_dynamic/SOURCE_FREEZE.json')['files'].items():assert sha(R/n)==h,n
    checks['all6645_old_scientific_sources_unchanged']=True
    checks['three_static_routes_remote_verified']=a.validate_static_anchor()
    checks['entry16_real_production_cases']=read(O/'ENTRY_QUALIFICATION.json')['passed']
    checks['original_19_runtime_fault_cases_reused_by_source_SHA']=read(R/'records/nav2_v884_20261108/ZERO_QUALIFICATION.json')['passed']
    checks['one_t0_main_success_repeat_order']=[t['task_id']for t in tasks]==['t0_we','main_we','repeat_we']
    checks['new_user_approved90min']=a.DURATION==5400. and read(O/'USER_APPROVAL.json')['latest_user_continuation']is True and read(O/'USER_APPROVAL.json')['standing_window_choice']=='新独立90分钟：原西向东动态主任务，成功后完整重复，首失败即停'
    for n in ['INDEPENDENT_GEOMETRY_AUDIT.json','WEST_EAST/RESULT.json']:
        p=R/'runs/v709_joint_reference_certificate'/n
        checks['existing_original_actor_construction_'+n]=p.is_file()
    # The real adapter is imported without a simulator. Its real create_vehicle seam
    # receives a fake vehicle module and must retain dynamic=True and the fixed phase.
    spec=importlib.util.spec_from_file_location('v892_dynamic_lazy_contract',C/'physical.py')
    physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
    calls=[];fake=types.ModuleType('vehicle');fake.initialize=lambda *args,**kwargs:None;fake.get_lidar_features=lambda *args,**kwargs:None
    v=types.SimpleNamespace(actor=types.SimpleNamespace(config=dict(maximum_speed_m_s=.08,amplitude_m=.25)),count=0,d=types.SimpleNamespace(time=0.),first_detection=None,scan=lambda:dict(ranges=[3.]*32))
    def create(out,case,seed,dynamic):calls.append((case,seed,dynamic));return v
    fake.Vehicle=create
    fakeout=O/'zero_only_fake_adapter';fakeout.mkdir(exist_ok=True)
    with patch.dict(sys.modules,vehicle=fake),patch.object(physical.engine.os,'chdir'):
        result=physical.create_vehicle(fakeout,tasks[1]);result.scan()
        checks['actual_dynamic_adapter_passes_true_not_static_false']=calls==[('WEST_EAST',10010001,True)]
        checks['actual_dynamic_adapter_uses_original_phase']=physical.engine.os.environ['PHASE_COURSE_PHASE']==str(tasks[1]['phase'])
        v.first_detection=dict(native_tick=0)
        try:result.scan();checks['real_t0_visible_actor_rejected']=False
        except AssertionError:checks['real_t0_visible_actor_rejected']=True
        v.first_detection=None
        old_getter=lambda *args,**kwargs:None;fake.get_lidar_features=old_getter
        v.scan=lambda:dict(ranges=[float(fake.get_lidar_features is physical.exact.get_lidar_features)]*32)
        try:physical.create_vehicle(fakeout,tasks[1]);checks['binding_rejects_changed_true_t0_packet']=False
        except AssertionError as error:checks['binding_rejects_changed_true_t0_packet']=str(error)=='TRUE_T0_SENSOR_VALUES_CHANGED'and fake.get_lidar_features is old_getter
    proof_path=fakeout/'EXACT_SENSOR_BINDING.json'
    proof=read(proof_path);proof['explicit_fake_qualification_not_a_real_model']=True;proof_path.write_text(json.dumps(proof,indent=2)+'\n')
    wire=policy_packet('fake',types.SimpleNamespace(count=0,d=types.SimpleNamespace(time=0.),body=lambda:(0.,0.,0.,0.,0.)),dict(native_tick=0,time=0.,ranges=[3.]*32,raw_lidar=[0.]*32,actor_xy=[1.,1.]),100.,100.,'WAITING')
    checks['real_policy_packet_strips_actor_and_raw_truth']=set(wire['scan'])=={'native_tick','time','ranges'}and not any(k in wire for k in ['actor','actor_xy','raw_lidar'])
    # Separate processes prove genuine entry imports and physical adapter selection.
    for name in ['native_worker.py','ros_worker.py','preflight_worker.py']:
        code='''import importlib.abc,runpy,sys,json
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0]in ['mujoco','rclpy','vehicle','physical']:raise AssertionError('FORBIDDEN_IMPORT '+fullname)
sys.meta_path.insert(0,Block());d=runpy.run_path(sys.argv[1],run_name='zero_entry_probe');t=json.loads((d['C']/'TASKS.json').read_text())[0]
try:(d['engine'].run if 'engine'in d else d['run'])(t,{},'NO_LIVE_AUTHORITY')
except RuntimeError as e:assert str(e)=='MODELS_NOT_AUTHORIZED',str(e)
else:raise AssertionError('UNAUTHORIZED_ENTRY')
print('ENTRY_REJECTED_BEFORE_MODEL')
'''
        p=subprocess.run([sys.executable,'-B','-c',code,str(C/name)],cwd=R,capture_output=True,text=True,timeout=15)
        checks[name+'_rejects_before_model_or_ros']=p.returncode==0
        if p.returncode:(O/(name+'.zero_error.console')).write_text(p.stdout+p.stderr)
    code="import runpy,importlib.util,sys;d=runpy.run_path(sys.argv[1],run_name='zero_probe');p=importlib.util.find_spec('physical');assert p.origin==str(d['C']/'physical.py'),p.origin;print('DYNAMIC_PHYSICAL_SELECTED')"
    p=subprocess.run([sys.executable,'-B','-c',code,str(C/'native_worker.py')],cwd=R,capture_output=True,text=True,timeout=15)
    checks['genuine_native_entry_resolves_new_dynamic_adapter']=p.returncode==0
    if p.returncode:(O/'physical_resolution.zero_error.console').write_text(p.stdout+p.stderr)
    from repeat_contract import canonical_setup
    import copy
    certificate=read(R/'runs/v709_joint_reference_certificate/WEST_EAST/RESULT.json')['selection']['certificate']
    setup=dict(actor=dict(phase_rad=tasks[0]['phase'],swept_envelope_reference=certificate),model_sha256='FIXED_PHYSICAL_MODEL',noise=dict(seed=10010001))
    timed=copy.deepcopy(setup);timed['actor']['swept_envelope_reference']['elapsed_s']+=10.;timed['actor']['swept_envelope_reference']['search']['wall_s']+=10.
    checks['only_construction_clocks_are_excluded_from_repeat_physics']=canonical_setup(setup)==canonical_setup(timed)
    changed=copy.deepcopy(setup);changed['actor']['phase_rad']+=.1;checks['changed_actor_phase_not_masked']=canonical_setup(setup)!=canonical_setup(changed)
    changed=copy.deepcopy(setup);changed['model_sha256']='CHANGED';checks['changed_model_not_masked']=canonical_setup(setup)!=canonical_setup(changed)
    changed=copy.deepcopy(setup);changed['actor']['swept_envelope_reference']['reference_path'][0][0]+=.1;checks['changed_construction_geometry_not_masked']=canonical_setup(setup)!=canonical_setup(changed)
    import math
    from packet_contract import policy_packet as wired_packet
    v=types.SimpleNamespace(count=10,d=types.SimpleNamespace(time=.1),body=lambda:(1.,2.,.3,0.,0.))
    packet=dict(native_tick=5,time=.05,xy=[.9,1.9],yaw=.2,ranges=[3.]*32,actor_xy=[999.,999.],raw_lidar=[-1.]*32)
    actual=wired_packet('fake',v,packet,10.,10.1,'RUNNING')
    checks['genuine_packet_carries_measurement_pose_not_new_body_pose']=actual['scan']['xy']==[.9,1.9]and actual['scan']['yaw']==.2 and actual['body'][:2]==[1.,2.]
    checks['new_packet_still_drops_actor_raw_truth']=set(actual['scan'])=={'native_tick','time','ranges','xy','yaw'}
    config=read(C/'A_motion.yaml');original=read(R/'experiments/v884_feasible_rpp/A_feasible.yaml');changed=[]
    def diff(a,b,path=''):
        if isinstance(a,dict)and isinstance(b,dict):
            for k in set(a)|set(b):
                if k not in a or k not in b:changed.append(path+'/'+k)
                else:diff(a[k],b[k],path+'/'+k)
        elif a!=b:changed.append(path)
    diff(original,config)
    allowed={f'/{x}/{x}/ros__parameters/{k}'for x in ['global_costmap','local_costmap']for k in ['plugins','use_maximum','motion_envelope','always_send_full_costmap']}|{'/controller_server/ros__parameters/general_goal_checker/xy_goal_tolerance','/bt_navigator/ros__parameters/default_nav_to_pose_bt_xml','/bt_navigator/ros__parameters/default_nav_through_poses_bt_xml'}
    checks['only_declared_map_layer_and_wait_BT_config_changes']=bool(changed)and set(changed)<=allowed
    layer=read(R/'records/nav2_v889_20261108/ROS_LAYER_QUALIFICATION.json')
    checks['genuine_global_local_layer_ingestion_and_replacement']=layer['passed']
    checks['genuine_saved_pose_full_route_with_forecast']=read(R/'records/nav2_v889_20261108/SAVED_FORECAST_PLAN_QUALIFICATION.json')['passed']
    checks['v891_support_contracts_and_genuine_ROS_passed']=all(read(R/'records/nav2_v891_20261108'/n)['passed'] for n in ['SUPPORT_QUALIFICATION.json','TERMINAL_QUALIFICATION.json','ROS_QUALIFICATION.json','CONTRACT_QUALIFICATION.json'])
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    checks['qualified_exact_lidar_source_SHA_matches']=sha(R/'experiments/v887_exact_lidar_software/exact_lidar.py')==read(R/'records/nav2_v887_20261108/QUALIFICATION.json')['new_lidar_source_sha256']
    checks['old_dynamic_failure_closed_and_new_software_qualification_passed']=read(R/'records/nav2_v886_20261108/COMPLETION.json')['closed']and read(R/'records/nav2_v887_20261108/QUALIFICATION.json')['passed']
    checks['no_model_window_created']=not(O/'AUTHORIZATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()and not(R/'runs/v858_nav2_verified/v892').exists()
    data=dict(passed=all(checks.values()),checks=checks,models=0,native_integrations=0,real_ros_servers=0,new_controller_core_revisions=0,new_causal_motion_mechanism_revisions=1,scope='Genuine new operation entries and original dynamic adapter under explicit fake dependencies; true physical t0 remains required')
    (O/'ZERO_QUALIFICATION.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data),flush=True)
    return 0 if data['passed']else 1
if __name__=='__main__':sys.exit(main())
