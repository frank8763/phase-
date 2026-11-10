"""Rebuild release-to-zero ownership from saved ingress and command evidence."""
import gzip,json
from pathlib import Path
def read(p):return json.loads(Path(p).read_text())
def audit(out):
    out=Path(out);profiles=read(out/'PROFILE_EXECUTION.json')['profiles'];rows=read(out/'RECOVERY_CORRIDORS.json')
    ingress=json.loads(gzip.decompress((out/'INGRESS.json.gz').read_bytes()))['receipts']
    tubes=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()));checks=[]
    for profile in profiles:
        pid=profile['profile_id'];event=next(r for r in rows if r.get('profile_id')==pid);h=event['atomic_handoff']
        release=next(r for r in ingress if r['packet']['kind']=='release_profile'and r['packet']['profile_id']==pid)
        command=release['packet']['resume_command'];proof=command['tube']
        accepted=next(r for r in ingress if r['packet']==command and r['decision']=='ACCEPTED')
        tube=next(r for r in tubes if r.get('handoff_stop')and r['profile_id']==pid and r['proof']==proof)
        assert profile['completed']and h['stop_ownership_until_ack']and command['v']==command['w']==proof['v']==proof['w']==0.
        assert release['decision']=='PROFILE_RELEASED'and accepted['native_tick']==release['native_tick']>=profile['end_native_tick']
        assert 0<=accepted['received_at']-command['issued_at']<=.05 and 0<=proof['body_age_s']<=.05
        assert h['sequence']==command['sequence']and h['zero_tube']==proof and tube['packet']['native_tick']==proof['body_native_tick']
        checks.append(dict(profile_id=pid,passed=True,sequence=command['sequence'],release_native_tick=release['native_tick'],zero_accepted_same_native_tick=True))
    return dict(passed=True,rows=checks,models=0,new_integrations=0)
