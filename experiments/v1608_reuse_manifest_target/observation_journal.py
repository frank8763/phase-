"""Every original observation, one charged append stream; draft/unqualified.

Original ACTUAL_ROS boundary and24MiB writer stay unchanged.20MiB is a stricter
sub-limit. No raw writable fd, model, observation filtering or authority here.
"""
import hashlib
import json
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2]
MAX_BYTES=20*1024**2
MAX_ROW=16384
MAX_ROWS=12001
sha=lambda data:hashlib.sha256(data).hexdigest()
encoded=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sync_readonly(path):
    path=Path(path);flags=os.O_RDONLY|(os.O_DIRECTORY if path.is_dir()else 0)
    descriptor=os.open(path,flags)
    try:os.fsync(descriptor)
    finally:os.close(descriptor)


class ObservationJournal:
    def __init__(self,output):
        output=Path(output).resolve();assert output.is_relative_to(R/'runs')
        folder=output/'causal_source';folder.mkdir(exist_ok=True)
        assert folder.resolve()==folder and not folder.is_symlink()
        self.path=folder/'OBSERVATIONS.jsonl';assert not self.path.exists()
        self.handle=self.path.open('xb')
        self.acknowledged_bytes=0;self.records=0;self.digest=hashlib.sha256()
        self.inflight=None;self.closed=False;self.failed=False
        self.close_errors=[]

    def append(self,row):
        assert not self.closed and not self.failed and self.inflight is None
        self.failed=True
        payload=encoded(row)+b'\n';size=len(payload)
        assert 0<size<=MAX_ROW and row['index']==self.records<MAX_ROWS
        assert self.path.stat().st_size==self.acknowledged_bytes
        assert self.acknowledged_bytes+size<=MAX_BYTES,'CAUSAL_JOURNAL_SUBLIMIT'
        offset=self.acknowledged_bytes
        self.inflight=dict(index=self.records,offset=offset,expected_bytes=size,payload_sha256=sha(payload))
        assert self.handle.write(payload)==size
        self.handle.flush();sync_readonly(self.path)
        if self.records==0:sync_readonly(self.path.parent)
        with self.path.open('rb')as stream:
            stream.seek(offset);saved=stream.read(size)
        assert saved==payload and json.loads(saved)==row,'CAUSAL_JOURNAL_DURABLE_SLICE_CHANGED'
        answer=dict(path=str(self.path.relative_to(R)),offset=offset,file_size=size,
            file_sha256=sha(payload),semantic_sha256=sha(encoded(row)))
        self.digest.update(payload);self.acknowledged_bytes+=size;self.records+=1
        self.inflight=None;self.failed=False
        return answer

    def prefix(self):
        assert not self.failed and self.inflight is None
        return dict(storage_kind='APPEND_ONLY_COMPLETE_CAUSAL_ROWS_V1',
            path=str(self.path.relative_to(R)),prefix_bytes=self.acknowledged_bytes,
            prefix_sha256=self.digest.hexdigest(),records=self.records)

    def close(self):
        errors=self.close_errors
        if not self.closed:
            for name,action in [('flush',self.handle.flush),('sync',lambda:sync_readonly(self.path)),('close',self.handle.close)]:
                try:action()
                except BaseException as error:errors.append(dict(stage=name,error=repr(error)))
            self.closed=True
        actual=self.path.stat().st_size
        descriptor_closed=bool(self.handle.closed)
        return dict(closed=True,descriptor_close_verified=descriptor_closed,
            passed=descriptor_closed and not errors and not self.failed and self.inflight is None and actual==self.acknowledged_bytes,
            errors=errors,acknowledged_bytes=self.acknowledged_bytes,actual_bytes=actual,
            acknowledged_records=self.records,acknowledged_prefix_sha256=self.digest.hexdigest(),
            inflight_append_unknown=self.inflight,failed=self.failed,
            no_unacknowledged_tail_promoted=True,models=0)


def read_prefix(output,description):
    expected=Path(output)/'causal_source/OBSERVATIONS.jsonl'
    path=R/description['path']
    assert description['storage_kind']=='APPEND_ONLY_COMPLETE_CAUSAL_ROWS_V1'
    assert path==expected and path.resolve()==expected and not path.is_symlink()
    size=description['prefix_bytes']
    assert type(size)is int and 0<size<=path.stat().st_size<=MAX_BYTES
    # Later observations may append to the same immutable prefix. They never
    # enter this request's fixed source snapshot or its receipt chain.
    with path.open('rb')as stream:raw=stream.read(size)
    assert len(raw)==size and sha(raw)==description['prefix_sha256']
    return raw


def row_at(raw,ref,*,path,offset):
    assert ref['path']==path and ref['offset']==offset
    size=ref['file_size'];assert type(size)is int and 0<size<=MAX_ROW
    data=raw[offset:offset+size]
    assert len(data)==size and data.endswith(b'\n')and sha(data)==ref['file_sha256']
    row=json.loads(data);assert sha(encoded(row))==ref['semantic_sha256']
    return row,offset+size
