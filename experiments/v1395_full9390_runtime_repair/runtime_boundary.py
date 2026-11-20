"""Explicit canonical cwd and failure-tolerant peer shutdown, no models."""
import os
from pathlib import Path
import signal
import socket
import subprocess
import json
R=Path(__file__).resolve().parents[2]
def initialize():
    os.chdir(R);assert Path.cwd()==R;return str(R)
def socket_owner(out):
    assert out.is_absolute() and out.is_relative_to(R/'runs')
    assert Path.cwd()==R,'RPC_REQUIRES_CANONICAL_CWD'
    address=str((out/'native_rpc.sock').relative_to(R));assert len(address.encode())<108,'UNIX_SOCKET_PATH_TOO_LONG'
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    try:sock.bind(address);sock.settimeout(.01)
    except BaseException:sock.close();raise
    return sock,address,str((out/'peer.sock').relative_to(R))
def close_peer(sock,address,target,peer,log,run_id):
    errors=[]
    def attempt(label,fn):
        try:fn()
        except BaseException as exc:errors.append(dict(operation=label,error=repr(exc)))
    if sock is not None and target is not None:attempt('send_stop',lambda:sock.sendto(json.dumps(dict(kind='STOP',run_id=run_id)).encode(),target))
    if peer is not None:
        try:peer.wait(timeout=8)
        except subprocess.TimeoutExpired:
            attempt('terminate_peer',lambda:os.killpg(peer.pid,signal.SIGTERM))
            try:peer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                attempt('kill_peer',lambda:os.killpg(peer.pid,signal.SIGKILL));attempt('wait_peer',lambda:peer.wait(timeout=3))
        except BaseException as exc:errors.append(dict(operation='wait_peer',error=repr(exc)))
    if log is not None:attempt('close_log',log.close)
    if sock is not None:attempt('close_socket',sock.close)
    if address is not None:attempt('unlink_socket',lambda:Path(address).unlink(missing_ok=True))
    return errors
