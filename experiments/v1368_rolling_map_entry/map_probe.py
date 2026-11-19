"""Actual controller/map lifecycle only; stationary recorded input, no goal/physics."""
import os
import subprocess
import sys
import time
import traceback
from component_context import *
from map_gate import inspect_map,snapshot
sys.path.insert(0,str(R/'experiments/v1366_canonical_timed_lattice'))
from probe import Fixture,NoPhysical,rclpy
from lifecycle_msgs.srv import ChangeState


class ActualSnapshotFixture(Fixture):
    def receive_map(self,message):self.map_received=snapshot(message)


def main():
    method=sys.argv[1];assert method in ['rpp','mppi'];out=O/('map_software_'+method);out.mkdir(exist_ok=False)
    source_tasks=read(R/'experiments/v1366_canonical_timed_lattice/SOFTWARE_TASKS.json')
    task=next(t for t in source_tasks if t['method']==method);saved=read(R/task['input_file']);grid=read(C/'COMMON_GRID.json')
    assert all(saved['map_grid'][key]==grid[key] for key in ['width','height','resolution','origin','data'])
    os.sched_setaffinity(0,{3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    started=time.monotonic();rclpy.init();node=ActualSnapshotFixture(task,saved);checks=[];server=None;log=(out/'controller.console').open('x');result=dict(passed=False,models=0,physical_native=0,software_only=True,no_action_sent=True)
    def wait(predicate,seconds):
        end=min(started+30,time.monotonic()+seconds)
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.005)
            assert server is None or server.poll() is None,'OWN_CONTROLLER_EXIT'
            if predicate():return
        raise TimeoutError('SOFTWARE_MAP_READY_TIMEOUT')
    try:
        server=subprocess.Popen(['/opt/ros/jazzy/lib/nav2_controller/controller_server','--ros-args','--params-file',str(C/(method+'_params.json'))],stdout=log,stderr=subprocess.STDOUT)
        wait(node.change.service_is_ready,15)
        for transition in [1,3]:
            req=ChangeState.Request();req.transition.id=transition;future=node.change.call_async(req);wait(future.done,15);assert future.result().success
        def ready():
            if node.map_received is None:return False
            proof=inspect_map(node.map_received,grid);checks.append(proof);return proof['passed']
        wait(ready,10)
        dump(out/'DELIVERED_COSTMAP.json',node.map_received)
        loaded=['libphase_executable_rpp.so'] if method=='rpp' else ['libphase_deadband_mppi.so','libcoherent.so','libmppi_controller.so']
        maps=Path('/proc/%d/maps'%server.pid).read_text();assert all(name in maps for name in loaded)
        assert node.rows==[]
        result.update(passed=True,actual_loaded_libraries=loaded,final_map_proof=checks[-1],commands=0)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=4)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        result.update(closed=True,controller_server_exited=server is None or server.poll() is not None,wall_s=time.monotonic()-started,no_physical_modules_loaded=not any(k in sys.modules for k in ['mujoco','vehicle','torch']))
        dump(out/'MAP_CHECKS.json',checks);dump(out/'RESULT.json',result);log.close();node.destroy_node();rclpy.shutdown()
    print(json.dumps(result));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
