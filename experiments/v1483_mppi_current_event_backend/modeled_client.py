"""Current-input-bound modeled engineeringMPPI RPC; no physical/model operations."""
import json
import math
from pathlib import Path
import socket
import time

R=Path(__file__).resolve().parents[2]


class ModeledClient:
    def __init__(self,out,*,run_id,input_sha256,controller_identity_sha256):
        out=Path(out).resolve()
        assert Path.cwd()==R and out.is_relative_to(R/'runs'), 'MODELED_RPC_REQUIRES_CANONICAL_OWNER'
        self.address=str((out/'modeled_owner.sock').relative_to(R));self.target=str((out/'peer.sock').relative_to(R))
        assert len(self.address.encode())<108 and len(self.target.encode())<108, 'MODELED_RPC_ENDPOINT_TOO_LONG'
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        try:self.socket.bind(self.address);self.socket.settimeout(.01)
        except BaseException:self.socket.close();raise
        assert isinstance(controller_identity_sha256,str)and len(controller_identity_sha256)==64
        self.run_id=run_id;self.input_sha256=input_sha256;self.controller_identity_sha256=controller_identity_sha256;self.sequence=0;self.accepted=-1
        self.sent={};self.replies=[];self.retired=[]

    def command(self,*,native_tick,body,input_sha256):
        assert input_sha256==self.input_sha256 and len(body)==5 and all(math.isfinite(x) for x in body)
        until=time.monotonic()+(55 if not self.replies else 3);next_send=0.;retired_count=0
        while time.monotonic()<until:
            if time.monotonic()>=next_send:
                value=dict(kind='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR',run_id=self.run_id,sequence=self.sequence,
                           native_tick=native_tick,body=body[:],input_sha256=input_sha256,controller_identity_sha256=self.controller_identity_sha256,sent_monotonic=time.monotonic())
                self.sent[self.sequence]=value;self.sequence+=1
                self.socket.sendto(json.dumps(value,allow_nan=False).encode(),self.target);next_send=time.monotonic()+.05
            try:reply=json.loads(self.socket.recv(65536))
            except socket.timeout:continue
            assert reply['run_id']==self.run_id and reply['input_sha256']==input_sha256 and reply['controller_identity_sha256']==self.controller_identity_sha256, 'MODELED_RPC_FOREIGN_INPUT_OR_CONTROLLER'
            assert type(reply['sequence']) is int and reply['sequence'] in self.sent, 'MODELED_RPC_UNKNOWN_SEQUENCE'
            source=self.sent[reply['sequence']]
            assert reply['native_tick']==source['native_tick'] and reply['body']==source['body'] and reply['not_measured_response'] is True, 'MODELED_RPC_CHANGED_SOURCE'
            assert reply['kind'] in ('COHERENT_MPPI_MODELED_COMMAND','MPPI_ACTION_DONE'), 'MODELED_RPC_WRONG_KIND'
            expired=False
            if reply['kind']=='COHERENT_MPPI_MODELED_COMMAND':
                age=time.monotonic()-reply['origin']['generated_monotonic'];assert math.isfinite(age) and age>=0., 'MODELED_RPC_FUTURE_COMMAND'
                expired=age>.2
            if source['native_tick']!=native_tick or reply['sequence']<=self.accepted or expired:
                self.retired.append(reply);retired_count+=1
                assert retired_count<256, 'MODELED_RPC_RETIREMENT_LIMIT'
                continue
            assert source['body']==body, 'MODELED_RPC_DIFFERENT_CURRENT_BODY'
            self.accepted=reply['sequence'];self.replies.append(reply);return reply
        raise TimeoutError('CURRENT_MODELED_MPPI_CALLBACK_TIMEOUT')

    def close(self):
        try:self.socket.sendto(json.dumps(dict(kind='STOP',run_id=self.run_id)).encode(),self.target)
        except OSError:pass
        finally:self.socket.close();Path(self.address).unlink(missing_ok=True)
