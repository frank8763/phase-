"""One output-only continuation, retaining V850 original absolute deadline."""
import fcntl,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from common import *
from engine import Stage,wait_bounded


def main():
    assert Path(sys.argv[0]).is_absolute(),'ABSOLUTE_REGISTERED_ENTRY_REQUIRED'
    lock=(ROOT/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(ROOT/'LAUNCH_CLAIM.json').open('x')as stream:stream.write('{}\n')
    assert not(ROOT/'ROUND_WINDOW.json').exists()and not PHASE.exists()
    assert read(ROOT/'QUALIFICATION.json')['passed']and read(ROOT/'OPERATIONS_CHECK.json')['passed'];unchanged()
    assert read(ROOT/'AUTHORIZATION.json')['window_s']==5400
    guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard)
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    inhibitor=None;process=None;status='STARTING';started=None;deadline=None;window=None
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(R/'runs/v690_visible_eight_meter/training_8m/proposer.json'),PHASE_PRIVATE_NATIVE_CAP='100000000')
    def execute(entry,args,label,cap,models):
        nonlocal process
        unchanged()
        if models:assert time.time()+cap+3<deadline
        dump(ROOT/'ACTIVE.json',dict(entry=entry,args=list(map(str,args)),cap_s=cap,models=models,started_unix=time.time(),absolute_model_deadline=deadline))
        with(ROOT/(label+'.console')).open('x')as stream:
            process=subprocess.Popen([str(R/'run_phase.sh'),str(C.relative_to(R)/entry),*map(str,args)],cwd=R,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            try:return wait_bounded(process,cap,models,deadline)
            finally:
                if process.poll()is None:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=2)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                process=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('V851_TERMINATED_NO_RETRY')))
    try:
        # Root timer starts before the sole first physical child launch and is
        # never reset by a stage or continuation. Sleep inhibition is OS-only.
        prior=read(R/'runs/v850_progress_consistent_return/ROUND_WINDOW.json');started=prior['started_unix'];deadline=prior['absolute_deadline_unix'];assert deadline==1794022529.6441045 and time.time()+2400<deadline;env['PHASE_MODEL_ABSOLUTE_DEADLINE']=str(deadline)
        window=dict(started_unix=started,continuation_started_unix=time.time(),absolute_deadline_unix=deadline,window_s=5400,round_closed=False,pid=os.getpid(),new24=0,original_V850_window_not_reset=True)
        dump(ROOT/'ROUND_WINDOW.json',window)
        with(ROOT/'inhibitor.console').open('x')as stream:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle:handle-lid-switch','--mode=block','--who=Phase','--why=Single bounded 90 minute Phase development',sys.executable,'-B',str(C/'os_watch.py'),'--pid',str(os.getpid()),'--entrypoint',str(Path(__file__).resolve()),'--deadline',str(deadline+3600)],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        time.sleep(.3);assert inhibitor.poll()is None,'OS_INHIBITOR_ENTRY_FAILED'
        dump(ROOT/'INHIBITOR.json',dict(pid=inhibitor.pid,root_pid=os.getpid(),model_deadline=deadline))
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V851_OUTPUT_ONLY_CONTINUATION',active_pid=os.getpid(),active_run=str(ROOT.relative_to(R)),active_entrypoint=str((C/'start.py').relative_to(R)),active_window=window,execution_window_closed=False,protocol=str((C/'PROTOCOL.md').relative_to(R)),decision_freeze=str((C/'CANDIDATE_FREEZE.json').relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',current)
        dump(ROOT/'LEDGER.json',dict(status='RUNNING_COMPONENT',closed=False,model_deadline=deadline,candidates=1,new24=0,training=0))
        (R/'REVIEW_PENDING').unlink()
        assert read(R/'runs/v850_progress_consistent_return/component01/INDEPENDENT_AUDIT.json')['passed']
        (R/'REVIEW_PENDING').write_bytes(guard)
        dump(ROOT/'LEDGER.json',dict(status='REUSED_COMPONENT_PASS_CONDITIONAL_ROUTES',closed=False,model_deadline=deadline,scientific_revisions_added=0,new24=0,training=0))
        stage=Stage(deadline);result=stage.run();status=result['status']
    except BaseException as error:
        status='STOPPED_EXCEPTION';dump(ROOT/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    finally:
        (R/'REVIEW_PENDING').write_bytes(guard)
        if inhibitor is not None and inhibitor.poll()is None:
            os.killpg(inhibitor.pid,signal.SIGTERM)
            try:inhibitor.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(inhibitor.pid,signal.SIGKILL);inhibitor.wait()
        if window is not None:window.update(round_closed=True,status=status,closed_unix=time.time());dump(ROOT/'ROUND_WINDOW.json',window)
        dump(ROOT/'LEDGER.json',dict(status=status,closed=True,no_more_models=True,candidates=1,new24=0,training=0))
        dump(ROOT/'COMPLETION.json',dict(status=status,model_deadline=deadline,window_s=5400,closed=True,no_automatic_restart=True,new24=0,training=0))
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',active_pid=None,active_run=None,active_entrypoint=None,active_window=None,execution_window_closed=True,report='docs/RPCCR_PROFILE_OUTPUT_V851_20261107_REPORT.md');current['v851_profile_output_continuation']=dict(status=status,closed=True,model_deadline=deadline,window_s=5400);dump(R/'CURRENT_EXPERIMENT.json',current)
        dump(ROOT/'ACTIVE.json',dict(completed=True,status=status))
    if window is not None:
        with(ROOT/'finalize.console').open('x')as stream:
            code=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=3600).returncode
        assert code==0 and(ROOT/'FINALIZED.json').exists(),'ZERO_MODEL_FINALIZER_FAILED_NO_MODEL_RETRY'


if __name__=='__main__':main()
