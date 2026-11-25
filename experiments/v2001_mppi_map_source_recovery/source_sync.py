"""Exactly one new source push30s/ref5s; never called for runtime."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v2001_mppi_map_source_recovery'
class Helper:
 @staticmethod
 def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
h=Helper()
def source_sync():
    assert not(O/'SOURCE_SYNC_CLAIM.json').exists()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    h.dump(O/'SOURCE_SYNC_CLAIM.json',dict(head=head,unix=time.time(),models=0,maximum_ref_s=5,no_retry=True,push_executed=True))
    proof=dict(head=head,remote_verified=False,models=0,retry_allowed=False,push_executed=False,new_evaluation_source=True)
    try:
        pushed=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,capture_output=True,text=True,timeout=30)
        proof['push_executed']=True
        proof['push_returncode']=pushed.returncode
        ref=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/git/ref/heads/main'],cwd=R,env=dict(__import__('os').environ,GODEBUG='http2client=0'),capture_output=True,text=True,timeout=5)
        proof['remote_verified']=ref.returncode==0 and json.loads(ref.stdout)['object']['sha']==head
    except subprocess.TimeoutExpired:proof['error']='BOUNDED_REF_TIMEOUT'
    h.dump(O/'SOURCE_SYNC_RESULT.json',proof);print(json.dumps(proof))
if __name__=="__main__":source_sync()
