"""A small owned local stream; no filesystem writers or model authority."""
import hashlib, json, os, socket, stat

class FrameChannel:
    def __init__(self,*,maximum_frames=12000):
        assert type(maximum_frames)is int and 1<=maximum_frames<=12000
        self.parent,self.child=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
        for endpoint in [self.parent,self.child]:
            endpoint.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,65536)
            endpoint.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,65536)
        self.parent.settimeout(10.)
        self.pid=os.getpid();self.maximum=maximum_frames
        self.frames=0;self.bytes=0;self.pending=None;self.closed=False;self.poisoned=False
        row=os.fstat(self.parent.fileno());assert stat.S_ISSOCK(row.st_mode)
        self.identity=(row.st_dev,row.st_ino)
        self.kernel_buffers=dict(send=self.parent.getsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF),receive=self.parent.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))

    def _guard(self):
        assert os.getpid()==self.pid,'FRAME_CHANNEL_FOREIGN_OWNER'
        assert not self.closed and not self.poisoned,'FRAME_CHANNEL_CLOSED_OR_POISONED'
        row=os.fstat(self.parent.fileno())
        assert stat.S_ISSOCK(row.st_mode)and(row.st_dev,row.st_ino)==self.identity,'FRAME_CHANNEL_FD_IDENTITY'

    def detach_child_endpoint(self):
        self._guard();self.child.close()

    def send(self,value):
        self._guard()
        assert self.pending is None,'FRAME_CHANNEL_REQUEST_INFLIGHT'
        assert self.frames<self.maximum,'FRAME_CHANNEL_COUNT_CAP'
        self.poisoned=True
        raw=json.dumps(value,allow_nan=False).encode()+b'\n'
        assert len(raw)<=1024**2,'FRAME_CHANNEL_BYTE_CAP'
        proof=dict(sequence=self.frames,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        self.parent.sendall(raw)
        self.frames+=1;self.bytes+=len(raw);self.pending=proof
        self.poisoned=False
        return dict(proof)

    def acknowledge(self,proof):
        self._guard()
        assert self.pending is not None and proof==self.pending,'FRAME_CHANNEL_WRONG_ACK'
        self.pending=None

    def finish_input(self):
        self._guard();assert self.pending is None,'FRAME_CHANNEL_REQUEST_INFLIGHT'
        self.parent.shutdown(socket.SHUT_WR)

    def close(self):
        if self.closed:return
        assert os.getpid()==self.pid,'FRAME_CHANNEL_FOREIGN_OWNER'
        self.closed=True;self.parent.close();self.child.close()
