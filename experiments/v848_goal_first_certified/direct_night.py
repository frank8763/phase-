"""One offline supervisor: wait for the already-running zero-model checks, freeze, then one campaign."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
import zipfile
from common import R,C,ROOT,PHASE,read,dump,sha

DEADLINE=1794009600.


def stop(process):
    if process is not None and process.poll()is None:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()


def main():
    with(ROOT/'DIRECT_NIGHT_CLAIM.json').open('x')as out:
        json.dump(dict(pid=os.getpid(),started_unix=time.time(),attempts=1,absolute_model_deadline_unix=DEADLINE),out)
    lock=(ROOT/'direct_night.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=(ROOT/'qualification/REVIEW_PENDING.before').read_bytes()
    assert not(ROOT/'LAUNCH_CLAIM.json').exists()
    inhibitor=None;child=None;status='WAITING_FOR_ZERO_MODEL_QUALIFICATION';failure=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('DIRECT_NIGHT_SUPERVISOR_TERMINATED_NO_RETRY')))
    try:
        with(ROOT/'direct_night_inhibitor.console').open('x')as out:
            inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle:handle-lid-switch','--mode=block','--who=Phase','--why=Bounded offline qualification and three-route night',sys.executable,'-B',str(C/'os_watch.py'),'--pid',str(os.getpid()),'--entrypoint',str(Path(__file__).resolve()),'--deadline',str(DEADLINE+14400)],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        time.sleep(.5);assert inhibitor.poll()is None,'DIRECT_NIGHT_SLEEP_INHIBITION_FAILED'
        dump(ROOT/'DIRECT_NIGHT_INHIBITOR.json',dict(pid=inhibitor.pid,supervisor_pid=os.getpid(),model_deadline_unix=DEADLINE,housekeeping_deadline_unix=DEADLINE+14400))
        dump(ROOT/'DIRECT_NIGHT_ACTIVE.json',dict(status=status,pid=os.getpid(),models_started=False,absolute_model_deadline_unix=DEADLINE))
        wait_until=min(time.time()+1500.,DEADLINE-6600.)
        while True:
            p=ROOT/'PREPARATION_CONTINUATION.json'
            if p.exists():
                assert read(p)['passed'],'ZERO_MODEL_QUALIFICATION_FAILED_NO_MODEL_LAUNCH'
                assert read(ROOT/'QUALIFICATION.json')['passed']
                break
            assert time.time()<wait_until,'ZERO_MODEL_QUALIFICATION_WAIT_EXPIRED_NO_MODEL_RETRY'
            time.sleep(5)
        assert(R/'REVIEW_PENDING').read_bytes()==guard,'QUALIFICATION_DID_NOT_RESTORE_ORIGINAL_GUARD'
        status='FREEZING';dump(ROOT/'DIRECT_NIGHT_ACTIVE.json',dict(status=status,models_started=False,absolute_model_deadline_unix=DEADLINE))
        with(ROOT/'prepare.console').open('x')as out:
            child=subprocess.Popen([sys.executable,'-B',str(C/'prepare.py')],cwd=R,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
            code=child.wait(timeout=600)
        assert code==0,'PREPARATION_FAILED_NO_MODEL_LAUNCH';child=None
        assert read(ROOT/'OPERATIONS_CHECK.json')['passed']
        status='CAMPAIGN_RUNNING'
        with(ROOT/'campaign.console').open('x')as out:
            child=subprocess.Popen([sys.executable,'-B',str(C/'start.py')],cwd=R,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
            dump(ROOT/'DIRECT_NIGHT_ACTIVE.json',dict(status=status,campaign_pid=child.pid,models_started=None,absolute_model_deadline_unix=DEADLINE))
            code=child.wait(timeout=max(1.,DEADLINE+14400-time.time()))
        assert code==0 and(ROOT/'COMPLETION.json').exists(),'CAMPAIGN_CLOSED_ABNORMALLY_NO_RETRY'
        child=None;status=read(ROOT/'COMPLETION.json')['status']
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        status='STOPPED_NIGHT_OPERATIONS_EXCEPTION_NO_RETRY';dump(ROOT/'DIRECT_NIGHT_ERROR.json',failure)
    finally:
        stop(child);stop(inhibitor)
        safe=False
        try:
            with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:
                fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB);safe=True
        except BlockingIOError:pass
        if safe:(R/'REVIEW_PENDING').write_bytes(guard)
        completion=dict(status=status,closed=True,closed_unix=time.time(),failure=failure,
            original_guard_restored_and_execution_lock_idle=safe,
            absolute_model_deadline_unix=DEADLINE,automatic_model_restart=False,
            new24=0,training=0,network_required=False,
            campaign_completion='runs/v848_goal_first_certified/COMPLETION.json'if(ROOT/'COMPLETION.json').exists()else None,
            finalized=(PHASE/'FINALIZED.json').exists())
        dump(ROOT/'DIRECT_NIGHT_COMPLETION.json',completion)
        if not(ROOT/'COMPLETION.json').exists():
            dump(ROOT/'LEDGER.json',dict(status=status,closed=True,active_simulation=not safe,no_more_models_or_integrations=True,new24=0,training=0))
            cur=read(R/'CURRENT_EXPERIMENT.json');cur.update(status='REVIEW_PENDING'if safe else'OPERATIONS_REVIEW_REQUIRED',state='REVIEW_PENDING'if safe else'OPERATIONS_REVIEW_REQUIRED',active_pid=None,active_entrypoint=None,execution_window_closed=True,active_run=None);dump(R/'CURRENT_EXPERIMENT.json',cur)
        cur=read(R/'CURRENT_EXPERIMENT.json');cur.setdefault('overnight_v848_20261106',{}).update(closed=True,status=status,night_completion=str((ROOT/'DIRECT_NIGHT_COMPLETION.json').relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',cur)
        final=read(PHASE/'FINALIZED.json')if(PHASE/'FINALIZED.json').exists()else None
        report=R/'docs/RPCCR_V848_DIRECT_OVERNIGHT_20261106_MORNING_REPORT.md'
        report.write_text('# V848 11月6日通宵实际结果\n\n'+json.dumps(dict(supervisor=completion,stage_final=final),ensure_ascii=False,indent=2)+'\n\n固定原三路线开发；新24/训练/算法对照均未授权启动。已执行、成功、失败、未执行及精确或未知积分分账以阶段独立终审为准。失败不继续依赖路线、不修补重启；原失败与截止保持。FINALIZED缺失即不能声称全证据完成。\n')
        # Closed child consoles and operation metadata get a separate immutable snapshot.
        target=R/'evidence/rpccr_v848_direct_night_closed_operations_20261106'
        if not target.exists():
            target.mkdir();inventory=[]
            files=[report,ROOT/'DIRECT_NIGHT_COMPLETION.json',ROOT/'DIRECT_NIGHT_CLAIM.json',ROOT/'DIRECT_NIGHT_ACTIVE.json',ROOT/'HANDOFF.md',R/'CURRENT_EXPERIMENT.json']
            for name in ['campaign.console','prepare.console','direct_night_inhibitor.console','DIRECT_NIGHT_ERROR.json','COMPLETION.json','LEDGER.json']:
                p=ROOT/name
                if p.is_file():files.append(p)
            with zipfile.ZipFile(target/'CLOSED_OPERATIONS.zip','x',compression=zipfile.ZIP_DEFLATED)as z:
                for p in files:
                    data=p.read_bytes();name=str(p.relative_to(R));z.writestr(name,data);inventory.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
            with zipfile.ZipFile(target/'CLOSED_OPERATIONS.zip')as z:
                for row in inventory:
                    data=z.read(row['path']);assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']
            dump(target/'MANIFEST.json',dict(inventory=inventory,source_and_decompressed_sha_verified=True,models=0,integrations=0,raw_deleted=False))
        print(json.dumps(completion),flush=True)


if __name__=='__main__':main()
