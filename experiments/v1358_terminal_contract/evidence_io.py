"""Cooperative peer closure and bounded, incremental evidence persistence."""
import json
import os
from pathlib import Path
import time


def atomic(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    def native(v):
        if hasattr(v,'tolist'):return v.tolist()
        if hasattr(v,'item'):return v.item()
        raise TypeError(type(v).__name__)
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=native)+'\n')
    temporary.replace(path)


class PeerClosure(Exception):pass


class Journal:
    def __init__(self,path):self.stream=Path(path).open('x',buffering=1)
    def append(self,value):
        self.stream.write(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n')
    def close(self):
        if not self.stream.closed:self.stream.flush();self.stream.close()


def persist(out,artifacts,result,*,closed):
    errors=[];out=Path(out)
    # First preserve the complete raw commands, before any controller shutdown.
    for name,value in artifacts:
        try:atomic(out/name,value)
        except BaseException as exc:errors.append(dict(file=name,error=repr(exc)))
    value=dict(result,closed=closed,evidence_write_errors=errors)
    if errors:value.update(passed=False,error='ROS_EVIDENCE_WRITE_FAILED')
    atomic(out/'ROS_RESULT.json',value)
    return value
