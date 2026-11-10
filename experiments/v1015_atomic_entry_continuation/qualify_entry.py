"""Exercise production readiness, STOP closure and denied authority; no model."""
import ast,copy,hashlib,importlib.abc,json,os,subprocess,sys,tempfile,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1015_atomic_entry_continuation'
sys.path[:0]=[str(C),str(R/'experiments/v1004_planned_input_navigation')]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('NO_MODEL_ENTRY_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel())
from budget import create,wait_ready
from closure import fatal_interface,supervise_workers
import authority
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
class Peer:
    def poll(self):return None
def main():
    O.mkdir(exist_ok=True)
    old=read(R/'experiments/v1006_navigation_entry_continuation/TASKS.json');tasks=read(C/'TASKS.json');rows=[]
    with tempfile.TemporaryDirectory(prefix='entry-',dir=O)as temp:
        d=Path(temp);dump(d/'NATIVE_READY.json',dict(origin_validated=True,native_tick=0,sim_time=0.))
        for a,b in zip(old,tasks):
            for k in a:
                if k not in ['run_id','output','socket_dir','baseline_output','preflight_output','nav2_params']:assert a[k]==b[k],k
            assert b['origin_native_tick']==0 and b['origin_sim_time']==0.
            assert b['baseline_output']in [t['output']for t in tasks]
            assert wait_ready(Peer(),d,create(b,time.time()+1000.),b)['native_tick']==0
            assert Path(b['output']).is_relative_to(R/'runs/v858_nav2_verified/v1015')
            rows.append(dict(task_id=b['task_id'],passed=True))
        wrong=copy.deepcopy(tasks[0]);wrong.pop('origin_native_tick')
        try:wait_ready(Peer(),d,create(tasks[0],time.time()+1000.),wrong)
        except KeyError:pass
        else:raise AssertionError('ORIGINAL_MISSING_ORIGIN_BUG_NOT_REPRODUCED')
        (d/'ros').mkdir();log=d/'ros/controller_server.console'
        log.write_text('Created goal checker general_goal_checker\nNo valid path found\n')
        assert fatal_interface(d)is None,'ORDINARY_REFUSAL_MUST_NOT_STOP_AS_INTERFACE'
        log.write_text('FollowPath called with goal_checker name  in parameter current_goal_checker, which does not exist.')
        assert fatal_interface(d)['reason']=='FATAL_NAV2_INTERFACE_BINDING'
        child=subprocess.Popen([sys.executable,'-c',"import pathlib,time,sys; p=pathlib.Path(sys.argv[1]); end=time.monotonic()+3;\nwhile not p.exists() and time.monotonic()<end:time.sleep(.005)\nsys.exit(0 if p.exists() else 1)",str(d/'PARENT_STOP_REQUEST.json')],start_new_session=True)
        result=supervise_workers([child],d,'software-closure',time.monotonic()+3,time.time()+10,closure_grace_s=1.)
        assert not result['passed']and result['failure']['reason']=='FATAL_NAV2_INTERFACE_BINDING'and not result['forced_process_groups']
        assert read(d/'PARENT_STOP_REQUEST.json')['run_id']=='software-closure'
        log.unlink();(d/'PARENT_STOP_REQUEST.json').unlink()
        child=subprocess.Popen([sys.executable,'-c','pass'],start_new_session=True)
        green=supervise_workers([child],d,'software-success',time.monotonic()+3,time.time()+10)
        assert green['passed']and not(d/'PARENT_STOP_REQUEST.json').exists()
    try:authority.root_authorized()
    except AssertionError as e:assert str(e)=='NEW_BOUNDED_CANDIDATE_NOT_AUTHORIZED'
    else:raise AssertionError('UNAPPROVED_MODEL_ADMITTED')
    import xml.etree.ElementTree as ET
    bt=ET.fromstring((C/'motion_bt.xml').read_text());follow=bt.findall('.//FollowPath')
    assert len(follow)==1 and follow[0].get('goal_checker_id')=='general_goal_checker'
    assert (C/'motion_bt.xml').read_bytes()==(R/'experiments/v1010_valid_path_software/motion_bt_valid_path.xml').read_bytes()
    tested=read(R/'experiments/v1010_valid_path_software/green_explicit.PARAMS.json');cfg=read(C/'A_forward.yaml')
    tested['bt_navigator']['ros__parameters']['default_nav_to_pose_bt_xml']=str(C/'motion_bt.xml');assert cfg==tested,'UNTESTED_PARAM_CHANGE'
    assert bt.find('.//ReactiveSequence/IsPathValid')is not None and bt.find('.//ReactiveSequence/Inverter/GlobalUpdatedGoal')is not None
    assert read(R/'records/nav2_v1010_20261110/FINAL_INDEPENDENT_AUDIT.json')['passed']is True
    assert (C/'repeat_contract.py').read_bytes()==(R/'experiments/v991_coordinated_components/repeat_contract.py').read_bytes()
    source={}
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p));source[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(passed=True,models=0,physical_integrations=0,readiness_rows=rows,original_missing_origin_reproduced=True,
        ordinary_refusal_not_structural_fault=True,actual_parent_watcher_stop_and_graceful_child_close=True,
        successful_child_not_marked_failed=True,unapproved_models_blocked=True,
        passed_complete_software_BT_exact=True,all_parameters_exact_except_BT_path=True,
        all_original_task_physics_fields_preserved=True,repeat_contract_unchanged=True,python_source_shas=source)
    dump(O/'ZERO_MODEL_QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['readiness_rows','python_source_shas']},indent=2))
if __name__=='__main__':main()
