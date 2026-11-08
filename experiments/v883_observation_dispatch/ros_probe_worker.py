"""Genuine Nav2/RPP saved-state diagnostic; no vehicle/model imports permitted."""
import importlib.util,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];OLD=R/'experiments/v881_timing_accounting_continuation'
sys.path[:0]=[str(C),str(OLD),str(R/'experiments/v862_ready_static')]
class NoModels:
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','vehicle','factory'}:raise RuntimeError('NO_VEHICLE_IMPORT '+fullname)
sys.meta_path.insert(0,NoModels())
import saved_path_server
sys.modules['planner_proxy']=saved_path_server
spec=importlib.util.spec_from_file_location('v883_software_bridge',C/'software_bridge.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine);engine.C=OLD
def authorized(task,receipt,now,sha):
    assert receipt['models_authorized']is False and receipt['software_diagnostic_only']is True and task['scope']=='RECORDED_STATE_SENSOR_PLAYBACK_NO_VEHICLE'
    assert task['run_id']==receipt['run_id']and receipt['started_unix']<=now<receipt['deadline_unix']and receipt['deadline_unix']-receipt['started_unix']<=70
    assert task['fixture_key']in ['150','175']
    return receipt['deadline_unix']
engine.authorized=authorized
if __name__=='__main__':sys.exit(engine.main())
