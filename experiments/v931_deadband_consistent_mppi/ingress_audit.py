"""Independent saved command/receiver/execution reconstruction; zero models."""
import math

def audit(journal,commands,run_id):
 receipts=journal['receipts'];execution=journal['execution'];assert len(execution)==len(commands)
 last=-1;phase='WAITING';command=None;j=0
 for i,(e,b)in enumerate(zip(execution,commands)):
  assert e['native_tick']==i+1 and math.isfinite(e['at'])
  while j<len(receipts)and receipts[j]['received_at']<=e['at']:
   r=receipts[j];j+=1;p=r['packet'];assert p['run_id']==run_id
   decision=r['decision']
   if decision=='ABORT':raise AssertionError('RECEIVER_ABORT')
   if p['kind']=='stop':phase='STOPPING'
   elif p['kind']=='arm'and phase=='WAITING':phase='RUNNING'
   elif p['kind']=='command':
    assert 0<=r['received_at']-p['issued_at']<=.2
    assert all(math.isfinite(p[k])for k in ['v','w'])and abs(p['v'])<=.100001 and abs(p['w'])<=abs(p['v'])/1.32+1e-6
    if phase=='STOPPING':assert decision=='POST_STOP_COMMAND_IGNORED'
    else:
     assert phase=='RUNNING'and decision=='ACCEPTED'and type(p['sequence'])is int and p['sequence']>last
     last=p['sequence'];command=p
  stale=phase!='RUNNING'or command is None or e['at']-command['issued_at']>.2
  expected=[0.,0.,True]if stale else[float(command['v']),float(command['w']),False]
  assert e['controls']==expected and b[1:3]==expected[:2]and b[5]==expected[2]
  assert e['sequence']==(None if command is None else command['sequence'])
 return dict(passed=True,executed_rows=len(execution),received_packets=len(receipts),scope='Independent receiver timestamp, expiry, phase, selected control and BODY_COMMANDS agreement')
