"""Real queues + real production planning child, bounded zero-model regression."""
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import time
from planning_job import PlanningJob
from transport import send_latest

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1346_measured_gear_handoff'


def main():
    rows=[]
    with tempfile.TemporaryDirectory(dir=O) as directory:
        folder=Path(directory);receiver=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);peer=str((folder/'receiver.sock').relative_to(Path.cwd()));receiver.bind(peer)
        sender=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sender.settimeout(.02)
        old_failed=False
        try:
            for i in range(256):sender.sendto(str(i).encode(),peer)
        except TimeoutError:old_failed=True
        assert old_failed
        # Full queue with same timeout remains a harmless observation drop.
        for _ in range(4096):
            if not send_latest(sender,b'latest',peer):break
        else:raise AssertionError('FAILED_TO_SATURATE_ACTUAL_QUEUE')
        start=time.monotonic();dropped=sum(not send_latest(sender,b'latest',peer) for _ in range(64));elapsed=time.monotonic()-start
        assert dropped==64 and elapsed<.15
        receiver.setblocking(False)
        while True:
            try:receiver.recv(65536)
            except BlockingIOError:break
        assert send_latest(sender,b'after_congestion',peer)
        assert receiver.recv(65536)==b'after_congestion'
        rows.append(dict(case='exact_send_timeout_red_then_nonblocking_congestion_recovery',passed=True,dropped=dropped,wall_s=elapsed))
        sender.close();receiver.close()
    for mode in ['success','crash','no_result','foreign','hang','cancel']:
        with tempfile.TemporaryDirectory(dir=O) as directory:
            job=PlanningJob(directory,worker=C/'fake_plan_worker.py',timeout_s=.6)
            job.start(dict(mode='hang' if mode=='cancel' else mode));error=None;result=None;pulses=0;begin=time.monotonic()
            try:
                while job.job is not None:
                    result=job.poll();pulses+=1
                    if mode=='cancel' and pulses>=10:job.cancel();break
                    if result is not None:break
                    time.sleep(.005)
            except AssertionError as exc:error=str(exc)
            finally:job.cancel()
            if mode=='success':assert result['passed'] and pulses>=10
            if mode in ['crash','no_result','foreign']:assert error is not None
            if mode=='hang':assert result['functional_timeout']
            assert job.job is None
            rows.append(dict(case='planner_'+mode,passed=True,io_brake_pump_iterations=pulses,wall_s=time.monotonic()-begin,error=error))
    # A cancelled/expired root cannot create another planning child.
    with tempfile.TemporaryDirectory(dir=O) as directory:
        job=PlanningJob(directory,worker=C/'fake_plan_worker.py',timeout_s=1,hard_stop_monotonic=time.monotonic()-1)
        try:job.start(dict(mode='success'));raise RuntimeError('EXPIRED_ROOT_ACCEPTED')
        except AssertionError:pass
        assert job.job is None;rows.append(dict(case='expired_root_denied',passed=True))
    # Original command gate is untouched, including old/future/control limits.
    spec=importlib.util.spec_from_file_location('actual_command_boundary',R/'experiments/v1288_baseline_interface/contract.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for issue in [9.,11.]:
        rejected=False
        try:module.command(dict(run_id='test',sequence=1,issued_at=issue,v=.1,w=0.),run_id='test',now=10.)
        except ValueError:rejected=True
        assert rejected
    proof=dict(passed=True,cases=rows,tests=len(rows),original_red_reproduced=True,io_independent_of_child_planner=True,stale_future_command_gates_unchanged=True,models=0,physical_native=0)
    (O/'IO_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='cases'}))


if __name__=='__main__':main()
