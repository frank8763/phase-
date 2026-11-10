"""Actual installed Nav2/BT action on an explicit nonphysical socket peer."""
import copy,gzip,importlib.abc,importlib.util,json,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1007_goal_checker_software_gate'
variant=sys.argv[1];assert variant in ['red_original','green_explicit']
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','physical','vehicle','factory'}:raise AssertionError('NO_VEHICLE_MODEL_IN_SOFTWARE_BT_PROBE '+name)
sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(R/'experiments/v1004_planned_input_navigation'),str(R/'experiments/v945_rpccr_observation_liveness'),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v884_feasible_rpp'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v883_observation_dispatch'),str(R/'experiments/v862_ready_static')]
spec=importlib.util.spec_from_file_location('v1007_real_ros_bridge',R/'experiments/v1004_planned_input_navigation/ros_bridge.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.authorized=lambda *args:time.time()+60.;engine.require_candidate_ready=lambda:None;engine.verify_sources=lambda *args:None
folder=O/variant;folder.mkdir(exist_ok=False);(folder/'physics').mkdir()
task=copy.deepcopy(json.loads((R/'experiments/v1004_planned_input_navigation/TASKS.json').read_text())[0]);task.update(run_id='v1007-'+variant,task_id=variant,
    output=str(folder),socket_dir=str(folder.relative_to(R)),nav2_params=str(C/(variant+'.PARAMS.json')),goal_xy=[-3.5,-2.],origin_native_tick=0,origin_sim_time=0.,
    stage='software_action_probe',wall_limit_s=8.,software_only_fixture=True)
(folder/'TASK.json').write_text(json.dumps(task,indent=2)+'\n')
with(folder/'peer.console').open('x')as log:
    peer=subprocess.Popen([sys.executable,'-B',str(C/'software_peer.py'),str(folder/'TASK.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
    until=time.monotonic()+3.
    while not(folder/'PEER_READY').exists():assert peer.poll()is None and time.monotonic()<until;time.sleep(.005)
    try:result=engine.run(task,{},'EXPLICIT_NO_MODEL_BT_RED_GREEN_PROBE')
    finally:
        try:peer.wait(timeout=3)
        except subprocess.TimeoutExpired:peer.terminate();peer.wait(timeout=2)
logs=(folder/'ros/controller_server.console').read_text();events=json.loads(gzip.decompress((folder/'PEER_EVENTS.json.gz').read_bytes()));commands=[p for p in events if p['kind']=='command'];moving=[p for p in commands if p['v']>0.]
empty=logs.count('FollowPath called with goal_checker name  in parameter')
passed=empty>0 and not moving if variant=='red_original'else empty==0 and bool(moving)and result.get('action_status')==4
report=dict(passed=passed,variant=variant,models=0,vehicle_native_integrations=0,physical_replays=0,synthetic_peer=True,installed_nav2_servers=True,
    empty_goal_checker_errors=empty,commands=len(commands),forward_commands=len(moving),action_status=result.get('action_status'),result_error=result.get('error'),
    exactly_one_XML_goal_checker_port_changed=variant=='green_explicit',physical_authority=False)
(O/(variant+'.RESULT.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
assert passed,'INSTALLED_NAV2_BT_REPRO_OR_FIX_NOT_PROVEN'
