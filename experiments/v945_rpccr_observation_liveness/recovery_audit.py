"""Saved RP-CCR alternative provenance; independent of online selector implementation."""
import gzip,json,math
from pathlib import Path
import numpy as np

def check(rows,goal):
 expected=[(0.,0.)]+[(v,v*k)for v in[-.1,-.05,.05,.1]for k in[-.758770385,0.,.758770385]]
 count=0;modes={}
 for row in rows:
  recovery=row.get('recovery')
  if recovery is None:continue
  count+=1;mode=recovery['mode'];modes[mode]=modes.get(mode,0)+1
  assert not row.get('wait_renewal')and row['wanted']!=[0.,0.]and row['source']['support_bounds']is not None
  assert recovery['nominal_proof']['passed']is False
  alternatives=recovery['alternatives'];assert len(alternatives)==13
  assert [tuple(a['control'])for a in alternatives]==expected
  for i,a in enumerate(alternatives):
   p=a['proof'];assert a['index']==i and a['passed']==p['passed']and [p['v'],p['w']]==a['control']
   assert p['body_native_tick']==row['packet']['native_tick']and p['source_native_tick']==row['source']['source_native_tick']and p['issued_at']==row['proof']['issued_at']
   qualified=p['static_lower_m']>=.155 and(p['dynamic_lower_m']is None or p['dynamic_lower_m']>=.155)and(p['terminal_cycle_lower_m']is None or p['terminal_cycle_lower_m']>=.155)
   assert qualified==p['passed']
  selected=recovery['selected']
  if selected is None:assert mode=='NO_NEW_CERTIFIED_CONTROL';continue
  matches=[a for a in alternatives if a['control']==list(selected)];assert len(matches)==1 and matches[0]['passed'];chosen=matches[0]
  assert chosen['proof']==row['proof']
  if mode=='CERTIFIED_PROGRESS_ALTERNATIVE':assert chosen['short_goal_progress_m']>1e-4
  elif mode=='CERTIFIED_CLEARANCE_RECOVERY':assert chosen['nominal_one_second_clearance_gain_m']>1e-4
  elif mode=='CERTIFIED_STOP_ONLY':assert selected==[0.,0.]or selected==(0.,0.)
  else:raise AssertionError('UNREGISTERED_RECOVERY_MODE')
 return dict(passed=True,recovery_decisions=count,modes=modes,safety_gate_unchanged=True,ranking_is_not_a_future_certificate=True)

def audit(out):
 out=Path(out);rows=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()));task=json.loads((out/'TASK.json').read_text());return check(rows,task['goal_xy'])
