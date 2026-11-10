"""Actual restored-origin ARM/causal publisher and fresh model-denial tests."""
import ast,copy,hashlib,importlib.abc,json,sys,time
from pathlib import Path
from types import SimpleNamespace as S
C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v982_precise_recovery_gate'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from authority import root_authorized
from native_contract import Startup
from motion_publisher import seed_history
from periodic_support import PeriodicSupport
from handshake import NODES

def main():
    tasks=json.loads((C/'TASKS.json').read_text());checks={}
    assert len(tasks)==2
    for i,task in enumerate(tasks):
        seed=json.loads((R/task['seed_history']).read_text())
        peer=S(tracker=S(),periodic=PeriodicSupport())
        proof=seed_history(peer,seed)
        checks[f'actual_causal_history_{i}']=proof['passed']and peer.tracker.when==seed['source']['source_scan_sim_time']
        now=time.monotonic();origin=task['origin_native_tick'];sim=task['origin_sim_time']
        packet=dict(kind='arm',run_id=task['run_id'],native_tick=origin,sim_time=sim,states={n:3 for n in NODES},checked_at={n:now for n in NODES},issued_at=now)
        startup=Startup(task['run_id']);startup._journals();startup.receive(packet,now,origin,sim)
        checks[f'actual_exact_origin_arm_{i}']=startup.phase=='RUNNING'and startup.events[-1]['event']=='COMPONENT_ORIGIN_ARM_VALIDATED'
        bad=Startup(task['run_id'])
        try:bad.receive(packet,now,origin+1,sim+.01)
        except AssertionError as e:checks[f'advanced_origin_red_{i}']=str(e)=='COMPONENT_ADVANCED_BEFORE_ARM'
        else:checks[f'advanced_origin_red_{i}']=False
        bad=copy.deepcopy(seed);bad['states'][-1]['native_tick']+=1
        try:seed_history(S(tracker=S(),periodic=PeriodicSupport()),bad)
        except AssertionError:checks[f'future_seed_red_{i}']=True
        else:checks[f'future_seed_red_{i}']=False
    try:root_authorized()
    except PermissionError as e:checks['physical_authority_absent_fail_closed']=str(e)=='V982_NEW_90MIN_PHYSICAL_APPROVAL_REQUIRED'
    else:checks['physical_authority_absent_fail_closed']=False
    import native_worker
    try:native_worker.engine.run({}, {}, '')
    except PermissionError as e:checks['actual_native_engine_denies_before_model_import']=str(e)=='V982_NEW_90MIN_PHYSICAL_APPROVAL_REQUIRED'
    else:checks['actual_native_engine_denies_before_model_import']=False
    checks['no_root_window_or_model_authority_created']=not(O/'USER_APPROVAL.json').exists()and not(O/'ROUND_WINDOW.json').exists()and not(O/'AUTHORIZATION.json').exists()
    for path in C.iterdir():
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
        assert not path.is_symlink(),'NO_AMBIGUOUS_SYMLINK_BINDINGS'
    checks['all_new_sources_parse_and_explicit_files']=True
    old=json.loads((R/'experiments/v981_tracking_evidence_closure/SOURCE_FREEZE.json').read_text())['files']
    checks['all_1562_old_frozen_files_unchanged']=all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in old.items())
    report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,physical_prefix_not_run=True,
                physical_ready=False,approval_required=True,fixed_tasks=[t['task_id']for t in tasks])
    (O/'ZERO_MODEL_ENTRY_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['passed']
if __name__=='__main__':main()
