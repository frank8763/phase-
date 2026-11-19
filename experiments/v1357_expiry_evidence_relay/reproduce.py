"""Reproduce the actual stale gate and wrapped-peer evidence loss, zero models."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def load(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    O.mkdir(exist_ok=True)
    old=load('old_stamped','experiments/v1356_bounded_motion_relay/stamped_contract.py')
    packet=dict(v=.05,w=0.,origin=old.local_zero(10.),observation_sequence=1,observation_native_tick=23200,observation_sampled_at=9.7)
    # Invalid local nonzero is not this bug: use the actual valid controller origin.
    packet['origin']=old.origin_from_header(1000000000,1010000000,10.)
    caught=None
    try:old.validate_delivery(packet,10.01)
    except AssertionError as exc:caught=str(exc)
    assert caught=='OBSERVATION_EXPIRED_AT_DELIVERY',caught
    monitor=load('old_monitor','experiments/v1356_bounded_motion_relay/worker_monitor.py')
    ros=load('ros_env','experiments/v856_nav2_foundation/ros_environment.py')
    folder=O/'old_peer_close';folder.mkdir(exist_ok=False)
    with (folder/'peer.console').open('x') as log:
        peer=subprocess.Popen(ros.command(['/usr/bin/python3.12','-B',str(C/'peer_fixture.py'),str(folder),'signal',str(time.monotonic()+15)]),cwd=R,env=ros.environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            end=time.monotonic()+5
            while not (folder/'READY.json').exists() and time.monotonic()<end:
                assert peer.poll() is None;time.sleep(.01)
            assert (folder/'READY.json').exists(),'FIXTURE_NOT_READY'
            native=subprocess.Popen([sys.executable,'-B','-c','pass'],start_new_session=True)
            result=monitor.monitor([peer,native],folder,remaining=lambda:10.,task_seconds=8)
        finally:monitor.terminate(peer)
    missing=not (folder/'ROS_COMMANDS.json').exists() and not (folder/'ROS_RESULT.json').exists()
    assert missing,'ORIGINAL_WRAPPER_TERMINATION_EVIDENCE_LOSS_NOT_REPRODUCED'
    proof=dict(reproduced=True,stale_observation_original_exception=caught,
         real_bubblewrap_peer_evidence_missing=missing,original_monitor=result,
         no_physical_models=True,models=0,physical_native=0,
         source='actual old validate_delivery and monitor; isolated wrapper with zero-model peer')
    (O/'ORIGINAL_REPRODUCTION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
