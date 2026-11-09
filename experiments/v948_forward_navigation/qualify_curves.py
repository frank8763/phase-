"""Two fixed saved causal states, no vehicle initialization or invented dynamics."""
import gzip
import importlib.abc
import json
import sys
from pathlib import Path
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('FORBIDDEN_MODEL_IMPORT '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v948_forward_navigation'
SAVED=ROOT/'runs/v858_nav2_verified/v945/main_we'
from forward_curve import construct
rows=json.loads(gzip.decompress((SAVED/'COMMAND_TUBES.json.gz').read_bytes()))
known=json.loads((SAVED/'physics/SETUP.json').read_text())['known']
chosen=[next(r for r in rows if np.linalg.norm(np.asarray(r['packet']['body'][:2])-[4.,-2.])<2.),rows[-1]]
results=[]
for row in chosen:
    result=construct(row['packet']['body'][:3],[4.,-2.],known,row['source']['periodic'])
    result['source_body_native_tick']=row['packet']['native_tick']
    result['source_periodic_tick']=row['source']['periodic']['source_tick']
    results.append(result)
    print(json.dumps({k:v for k,v in result.items()if k!='reference'}),flush=True)
result=dict(reference_geometry_passed=all(r['passed']for r in results),physical_ready=False,
            models=0,integrations=0,cases=results,unchanged_original_goal=[4.,-2.])
(OUT/'CURVE_INTERVAL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
