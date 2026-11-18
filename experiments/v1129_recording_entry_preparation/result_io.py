"""Strict JSON normalization; serialize fully before touching an output file."""
import json,os
from pathlib import Path
import numpy as np

def scalar(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    raise TypeError('Unsupported record value: '+type(value).__name__)

def encode(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2,default=scalar)+'\n'

def dump(path,value):
    content=encode(value)
    path=Path(path);temporary=path.with_name(path.name+'.pending.'+str(os.getpid()))
    try:
        with temporary.open('x')as stream:
            stream.write(content);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()
