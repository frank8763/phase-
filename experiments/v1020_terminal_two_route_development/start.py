"""Start exactly once after an explicit new approval; no vehicle imports here."""
import fcntl,json,os,subprocess,sys,time
from datetime import datetime
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1020_terminal_two_route_development';ROOT=R/'runs/terminal_two_route_20261110'
sys.path.insert(0,str(C))
from authority import read,sha
from handshake import verify_sources
def main():
    approval=read(ROOT/'APPROVAL.json');assert approval['models_authorized']is True and approval['new_night_authorized']is True,'NEW_USER_APPROVAL_REQUIRED'
    assert not(ROOT/'ROUND_WINDOW.json').exists()and not(O/'CAMPAIGN_CLAIM.json').exists()and not(ROOT/'COMPLETION.json').exists(),'ROOT_ALREADY_ATTEMPTED'
    assert approval['source_freeze_sha256']==sha(C/'SOURCE_FREEZE.json');verify_sources(R,C/'SOURCE_FREEZE.json')
    assert read(O/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(O/'AUTHORITY_QUALIFICATION.json')['passed']and read(O/'INSTALLED_IMPORT_QUALIFICATION.json')['passed']and read(O/'BACKEND_ENTRY_QUALIFICATION.json')['passed']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(R/'CURRENT_EXPERIMENT.json')['status']=='REVIEW_PENDING'
    now=time.time();end=1794358800.;assert end-now>=900.,'INSUFFICIENT_NEW_WINDOW'
    w=dict(started_unix=now,deadline_unix=end,started_iso=datetime.fromtimestamp(now).astimezone().isoformat(),deadline_iso=datetime.fromtimestamp(end).astimezone().isoformat(),
        absolute_overnight_deadline_unix=1794358800.,source_freeze_sha256=approval['source_freeze_sha256'],old_windows_not_reopened=True)
    with(ROOT/'ROUND_WINDOW.json').open('x')as stream:json.dump(w,stream,indent=2);stream.write('\n')
    fcntl.flock(lock,fcntl.LOCK_UN)
    # Native workers also retain independent absolute alarms and per-task budgets.
    # Extra outer time is for zero-model finalization; it grants no model time.
    model_end=1794358800. if approval['conditional_overnight']else end
    with(ROOT/'campaign.console').open('x')as log:
        job=subprocess.Popen(['systemd-inhibit','--what=idle:sleep','--mode=block','--why=Phase bounded overnight V1020','timeout','--signal=TERM','--kill-after=60',str(max(1,int(model_end-now+1260))),sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    receipt=dict(pid=job.pid,started_unix=now,prerequisite_deadline_unix=end,model_hard_stop_unix=model_end,offline_capable=True)
    (ROOT/'START_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
