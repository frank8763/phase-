"""Actual isolated cwd/socket red case and exact production-finally injection."""
import ast
import errno
import json
import os
from pathlib import Path
import signal
import socket
import sys
import time
from types import SimpleNamespace
from runtime_boundary import R,initialize,socket_owner,close_peer
from evidence_io import atomic
C=Path(__file__).resolve().parent;O=R/'runs/v1395_full9390_runtime_repair';RAW=R/'runs/v858_nav2_verified/v1395'
def main():
    out=RAW/'runtime_qualification';out.mkdir(parents=True,exist_ok=False);initial=Path.cwd()
    assert initial==Path('/home/linghu/catkin_ws/src/mk-mini'),'QUALIFY_EXACT_LEGACY_CWD'
    address=str((out/'native_rpc.sock').relative_to(R));red=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    try:red.bind(address)
    except FileNotFoundError as exc:assert exc.errno==errno.ENOENT
    else:raise AssertionError('LEGACY_CWD_RED_CASE_NOT_REPRODUCED')
    finally:red.close()
    initialize();sock,actual,target=socket_owner(out);sender=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sender.sendto(b'canonical-owned-socket',actual);assert sock.recv(100)==b'canonical-owned-socket';sender.close()
    assert close_peer(sock,actual,None,None,None,'fixture')==[] and not (R/actual).exists()
    try:raise RuntimeError('ORIGINAL_FAILURE_MUST_SURVIVE')
    except RuntimeError as error:
        errors=close_peer(None,None,None,None,None,'fixture');assert str(error)=='ORIGINAL_FAILURE_MUST_SURVIVE' and errors==[]
    class BadSocket:
        def sendto(self,*_):raise OSError('fixture socket stopped')
        def close(self):pass
    errors=close_peer(BadSocket(),None,'missing-fixture-endpoint',None,None,'fixture');assert len(errors)==1 and errors[0]['operation']=='send_stop'
    # Execute the exact production finally statements with explicit no-model
    # objects. This catches the original masking error and evidence omission.
    tree=ast.parse((C/'native.py').read_text());run=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run');node=next(x for x in run.body if isinstance(x,ast.Try));folder=out/'finally_fixture';folder.mkdir()
    result=dict(passed=False,error='ORIGINAL_FAILURE_MUST_SURVIVE',analytical_native=0,canonical_vehicle_initializations=0)
    scope=dict(finishing=False,result=result,rpc_socket=None,rpc_address=None,target=None,peer_job=None,peer_log=None,task=dict(run_id='early-failure'),close_peer=close_peer,out=folder,dump=atomic,journal=[],commands=[],observations=[],reserve_rows=[],reserve_states=[],reserve_ctrl=[],creating=False,in_step=False,v=None,signal=signal,sources=lambda:True,time=time,started=time.monotonic())
    exec(compile(ast.Module(body=node.finalbody,type_ignores=[]),str(C/'native.py'),'exec'),scope)
    saved=json.loads((folder/'RESULT.json').read_text());assert saved['error']=='ORIGINAL_FAILURE_MUST_SURVIVE' and saved['actual_total_native']==0 and saved['own_replay_native'] if 'own_replay_native' in saved else saved['error']=='ORIGINAL_FAILURE_MUST_SURVIVE'
    assert saved['closed'] and saved['peer_close_errors']==[] and (folder/'APPLIED_JOURNAL.json').exists() and (folder/'RESULT_PROGRESS.json').exists()
    proof=dict(passed=True,actual_initial_cwd=str(initial),old_relative_socket_ENOENT_reproduced=True,canonical_cwd_short_socket_real_roundtrip=True,none_partial_peer_shutdown_preserves_first_error=True,exact_production_finally_early_failure_saves_result_and_journal=True,physical_models=0,physical_native=0,analytical_native=0)
    atomic(O/'RUNTIME_QUALIFICATION.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
