"""Separate reconstruction of received/ignored commands and every actual step."""
import gzip,json,math
from pathlib import Path
import numpy as np

def permission(p,tick):
    dt=(tick-p['body_native_tick'])*.01
    return p.get('passed')is True and 0<=p['body_age_s']<=.05 and dt>=0 and (dt<=2.25+p['body_age_s']+1e-8 or (p.get('terminal_cycle_qualified')is True and math.isfinite(p.get('terminal_cycle_lower_m',math.nan)) and p['terminal_cycle_lower_m']>=.155))

def check(data,proofs,recorded,run_id):
    checks=dict(journal_present=bool(data['receipts']),received_matches_dispatched=True,original_50ms_admission=True,late_discards_keep_old_anchor=True,sequence_order=True,every_native_step=True,control_expiry=True,original_empirical_residual=True,completed_execution=True,no_rejected_packet=True)
    active=None;seq=-1;phase='WAITING';received={};events=data['receipts'];i=0;discarded=0;max_delay=0.
    for tick,step in enumerate(data['execution'],1):
        while i<len(events)and events[i]['native_tick']<tick:
            e=events[i];i+=1;p=e['packet'];prior=None if active is None else active['sequence']
            checks['sequence_order'] &= e['prior_sequence']==prior and p.get('run_id')==run_id
            if p['kind']=='arm':phase='RUNNING'
            elif p['kind']=='stop':phase='STOPPING'
            elif p['kind']=='command':
                age=e['received_at']-p['issued_at'];max_delay=max(max_delay,age)
                checks['received_matches_dispatched'] &= p['tube'] in proofs and p['v']==p['tube']['v']and p['w']==p['tube']['w']and p['issued_at']==p['tube']['issued_at']
                checks['sequence_order'] &= p['sequence']>seq and p['tube']['source_native_tick']<=p['tube']['body_native_tick']<=e['native_tick']
                seq=p['sequence']
                if e['decision']=='ACCEPTED':
                    checks['original_50ms_admission'] &= phase=='RUNNING' and 0<=age<=.05
                    active=p;received[p['sequence']]=p
                elif e['decision']=='LATE_NEW_COMMAND_DISCARDED':
                    discarded+=1
                    checks['late_discards_keep_old_anchor'] &= .05<age<=.2 and active is not None and permission(active['tube'],e['native_tick']) and e['retained_sequence']==prior
                else:checks['no_rejected_packet']=False
            checks['sequence_order'] &= e['retained_sequence']==(None if active is None else active['sequence'])
        checks['every_native_step'] &= step['native_tick']==tick and tick<=len(recorded)and step['phase']==phase and step['sequence']==(None if active is None else active['sequence'])
        expected=[0.,0.,True]if phase!='RUNNING'or active is None or step['at']-active['issued_at']>.2 else[active['v'],active['w'],False]
        checks['control_expiry'] &= step['controls']==expected
        checks['completed_execution'] &= step['completed']
        if active is not None and tick<=len(recorded):
            p=active['tube'];dt=(tick-p['body_native_tick'])*.01;u=min(dt,.2);b=p['body'];a=b[2]+p['w']*u
            if abs(p['w'])<1e-10:xy=np.array(b[:2])+p['v']*u*np.array([math.cos(b[2]),math.sin(b[2])])
            else:xy=np.array(b[:2])+p['v']/p['w']*np.array([math.sin(a)-math.sin(b[2]),math.cos(b[2])-math.cos(a)])
            r=recorded[tick-1];d=p['body_age_s']+.05
            checks['original_empirical_residual'] &= permission(p,tick)and abs(r[3])<=.13 and abs(r[4])<=.16 and np.linalg.norm(r[:2]-xy)<=p['residual_position_m']+.13*d+1e-8 and abs(math.atan2(math.sin(r[2]-a),math.cos(r[2]-a)))<=.035+.16*d+1e-8
    checks['every_native_step'] &= len(data['execution'])==len(recorded)
    checks['no_rejected_packet'] &= all(e['decision']!='REJECTED_ABORT'for e in events)
    checks['trailing_packets_no_unchecked_command']=all(e['packet']['kind']!='command'for e in events[i:])
    return dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},received_admissions=len(received),late_new_discards=discarded,native_execution_records=len(data['execution']),maximum_received_delivery_age_s=max_delay)

def audit_ingress(out):
    out=Path(out);data=json.loads(gzip.decompress((out/'INGRESS.json.gz').read_bytes()))
    rows=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()));proofs=[r['proof']for r in rows if r['proof']['passed']]
    with np.load(out/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'];v=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));recorded=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    return check(data,proofs,recorded,json.loads((out/'TASK.json').read_text())['run_id'])
