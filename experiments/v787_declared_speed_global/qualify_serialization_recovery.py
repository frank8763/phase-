"""Preserve original zero-model NumPy JSON failure; normalize scalars only."""
import json,time,hashlib
from pathlib import Path
import numpy as np
own=Path(__file__).parent;repo=own.parents[1];old=json.loads((repo/'runs/v787_speed_prior_qualification/ROUND_WINDOW.json').read_text());assert old['round_closed'];deadline=old['absolute_deadline_unix'];assert time.time()+30<deadline
original_dumps=json.dumps
def default(value):
 if isinstance(value,np.generic):return value.item()
 raise TypeError(type(value).__name__)
def dumps(value,*args,**kwargs):kwargs.setdefault('default',default);return original_dumps(value,*args,**kwargs)
json.dumps=dumps
code=(own/'qualify_prior.py').read_text().replace("'runs/v787_speed_prior_qualification'", "'runs/v787_speed_prior_qualification_recovered'").replace('started=time.time();signal.signal',f'started={old["started_unix"]!r};signal.signal').replace('signal.alarm(300);',f'signal.alarm(max(1,int({deadline!r}-time.time())));')
namespace={'__name__':'__main__','__file__':str(own/'qualify_prior.py')};exec(compile(code,str(own/'qualify_prior.py'),'exec'),namespace)
