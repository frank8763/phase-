"""Unattended offline queue; all model work ends at the original fixed 20:00."""
import fcntl,os,signal,subprocess,sys,time,traceback
from common import *
from engine import Stage,wait_bounded,stop,BudgetStop


def main():
    assert Path(sys.argv[0]).is_absolute();assert time.time()<DEADLINE-1200
    lock=(ROOT/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(ROOT/'LAUNCH_CLAIM.json').open('x')as f:f.write(json.dumps(dict(started_unix=time.time(),pid=os.getpid(),fixed_deadline=DEADLINE))+'\n')
    assert read(ROOT/'QUALIFICATION.json')['passed']and read(ROOT/'OPERATIONS_CHECK.json')['passed'];unchanged()
    guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard)
    with(R/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});process=None;inhibitor=None;status='STARTING';started=time.time();branches=[];pre=[];current_stage=None;backend=False
    window=dict(started_unix=started,absolute_deadline_unix=DEADLINE,absolute_deadline_local='2026-11-07 20:00:00+08:00',pid=os.getpid(),round_closed=False,new24=0)
    dump(ROOT/'ROUND_WINDOW.json',window)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',PHASE_PROPOSAL_MODEL=str(R/'runs/v690_visible_eight_meter/training_8m/proposer.json'),PHASE_PRIVATE_NATIVE_CAP='100000000',PHASE_RECOVERY_ABLATION='FULL',PHASE_MODEL_ABSOLUTE_DEADLINE=str(DEADLINE))
    def ledger():dump(ROOT/'LEDGER.json',dict(status=status,closed=False,deadline=DEADLINE,branches=branches,backend_launched=backend,new24=0,training=0))
    def child(script,label,variant,commit,cap):
        nonlocal process
        unchanged()
        if time.time()+cap+3>=DEADLINE:raise BudgetStop('NO_COMPLETE_COMPONENT_BUDGET')
        dump(ROOT/'ACTIVE.json',dict(script=script,variant=variant,cap_s=cap,started_unix=time.time(),deadline=DEADLINE))
        with(ROOT/(label+'.console')).open('x')as f:
            process=subprocess.Popen([str(R/'run_phase.sh'),str(C.relative_to(R)/script),*([variant]if script=='component.py'else[])],cwd=R,env=dict(env,PHASE_MANEUVER_COMMIT_NATIVE=str(commit)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:return wait_bounded(process,cap,True,DEADLINE)
            finally:stop(process);process=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('CAMPAIGN_TERMINATED_NO_RETRY')))
    try:
        with(ROOT/'inhibitor.console').open('x')as f:inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle:handle-lid-switch','--mode=block','--who=Phase','--why=Offline bounded Phase daytime research until 20:00',sys.executable,'-B',str(C/'os_watch.py'),'--pid',str(os.getpid()),'--entrypoint',str(Path(__file__).resolve()),'--deadline',str(DEADLINE+3600)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        time.sleep(.3);assert inhibitor.poll()is None,'OS_INHIBITOR_FAILED_BEFORE_MODELS';dump(ROOT/'INHIBITOR.json',dict(pid=inhibitor.pid,root_pid=os.getpid(),model_deadline=DEADLINE))
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V853_UNATTENDED_DAYTIME',active_pid=os.getpid(),active_run=str(ROOT.relative_to(R)),active_entrypoint=str((C/'start.py').relative_to(R)),active_window=window,execution_window_closed=False,protocol=str((C/'PROTOCOL.md').relative_to(R)),decision_freeze=str((C/'CANDIDATE_FREEZE.json').relative_to(R)));dump(R/'CURRENT_EXPERIMENT.json',current)
        (R/'REVIEW_PENDING').unlink();status='RUNNING_PREDECLARED_COMPONENTS_AND_ROUTES';ledger()
        for variant,commit in VARIANTS:
            if time.time()+905>=DEADLINE:status='ABSOLUTE_BUDGET_STOP';break
            row=dict(variant=variant,commit_native=commit,component_started=True,route_started=False,status='COMPONENT_RUNNING');branches.append(row);ledger()
            code=child('component.py',variant+'_component',variant,commit,905);row['component_exit']=code;ledger();assert code==0,'COMPONENT_SAFETY_SOURCE_OR_EVIDENCE_EXCEPTION'
            component=read(ROOT/('component_'+variant)/'RESULT.json');row['component_passed']=component['passed']
            if not component['passed']:row['status']='SAFE_COMPONENT_FUNCTIONAL_NOT_PASSED';ledger();continue
            # Independent computation branch is scheduled early so it does not
            # silently starve behind long route runs; it never modifies policy.
            if not backend and time.time()+610<DEADLINE:
                backend=True;ledger();assert child('backend_qualification.py','cpu_batch',variant,commit,605)==0,'BACKEND_OPERATION_EXCEPTION_STOP_ALL';row['backend_status']=read(ROOT/'cpu_batch_qualification/RESULT.json')['status'];ledger()
            current_stage=Stage(variant,commit);row['route_started']=True;ledger()
            if not pre:
                for task in tasks():current_stage.t0(task)
                pre=current_stage.pre.copy()
            row['status']=current_stage.routes(pre);row['records']=current_stage.rows;ledger();current_stage=None
        else:status='ALL_PREREGISTERED_BRANCHES_CLOSED'
    except BudgetStop as e:status='ABSOLUTE_BUDGET_STOP';dump(ROOT/'BUDGET_STOP.json',dict(reason=str(e),time=time.time()))
    except BaseException as e:
        status='FATAL_ANOMALY_ALL_MODEL_BRANCHES_STOPPED';dump(ROOT/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),no_model_retry=True))
    finally:
        stop(process)
        if current_stage is not None:stop(current_stage.process)
        (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,closed_unix=time.time());dump(ROOT/'ROUND_WINDOW.json',window)
        dump(ROOT/'LEDGER.json',dict(status=status,closed=True,no_more_models=True,branches=branches,backend_launched=backend,deadline=DEADLINE,new24=0,training=0));dump(ROOT/'COMPLETION.json',dict(status=status,closed=True,branches=branches,no_automatic_restart=True,model_deadline=DEADLINE,new24=0,training=0))
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_pid=None,active_run=None,active_entrypoint=None,active_window=None,execution_window_closed=True,report='docs/RPCCR_DAYTIME_V853_20261107_REPORT.md');current['v853_daytime_20261107']=dict(status=status,closed=True,model_deadline=DEADLINE,new24=0);dump(R/'CURRENT_EXPERIMENT.json',current);dump(ROOT/'ACTIVE.json',dict(completed=True,status=status))
        stop(inhibitor)
    with(ROOT/'finalize.console').open('x')as f:
        p=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=3600)
    assert p.returncode==0 and(ROOT/'FINALIZED.json').exists(),'ZERO_MODEL_FINALIZATION_FAILED_NO_MODEL_RESTART'


if __name__=='__main__':main()
