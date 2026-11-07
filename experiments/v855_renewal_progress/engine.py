"""Run all original applicable audits with independently fixed task registries."""
import fcntl,os,shutil,signal,subprocess,time
from common import *
from repeat import compare


def wait_bounded(p,cap,models,deadline):
    until=time.monotonic()+cap
    while True:
        remaining=until-time.monotonic()
        if models:remaining=min(remaining,deadline-time.time())
        if remaining<=0:raise TimeoutError('ABSOLUTE_CHILD_DEADLINE')
        assert shutil.disk_usage(ROOT).free>=25*1024**3,'EVIDENCE_DISK_LOW'
        try:return p.wait(timeout=min(10,remaining))
        except subprocess.TimeoutExpired:pass


def stop(p):
    if p is not None and p.poll()is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()


class FunctionalStop(Exception):pass
class BudgetStop(Exception):pass


class Stage:
    def __init__(self,variant,commit):
        self.variant=variant;self.phase=ROOT/variant;self.phase.mkdir(exist_ok=False);self.rows=[];self.pre=[];self.process=None
        self.env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(R/'runs/v690_visible_eight_meter/training_8m/proposer.json'),PHASE_MODEL_ABSOLUTE_DEADLINE=str(DEADLINE),PHASE_PRIVATE_NATIVE_CAP='100000000',PHASE_NAV_SOFT_WALL_S='5400',PHASE_MANEUVER_COMMIT_NATIVE=str(commit),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        dump(self.phase/'SOURCE_FREEZE.json',{p.name:sha(p)for p in W.glob('*.py')});dump(self.phase/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in W.glob('*.md')});dump(self.phase/'ROUND_WINDOW.json',dict(absolute_deadline_unix=DEADLINE,started_unix=time.time(),round_closed=False,commit_native=commit));self.save()
    def save(self):dump(self.phase/'RESULTS.json',self.rows);dump(self.phase/'PREFLIGHTS.json',self.pre)
    def set_task(self,t):self.env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']),PHASE_FIELD_CASE=t['case_id'],PHASE_COURSE_PHASE=str(t['phase']))
    def execute(self,script,args,log,cap,models=False,on_launch=None):
        unchanged();assert shutil.disk_usage(ROOT).free>=25*1024**3
        if models and not model_fits(DEADLINE,time.time(),cap):raise BudgetStop('INSUFFICIENT_REMAINING_MODEL_WINDOW')
        dump(self.phase/'ACTIVE.json',dict(script=script,args=list(map(str,args)),models=models,cap_s=cap,started_unix=time.time(),deadline=DEADLINE));held=None
        try:
            if script!='run_static.py':held=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            command=[str(R/'run_phase.sh')]
            if script=='run_static.py':command+=[str(W.relative_to(R)/script)]
            elif script=='replay_native_audit.py':command+=['experiments/staged_90_then12_20261106/worker_entry.py',W.name,script]
            else:
                command+=[str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(args[0])]
                if script=='audit_run.py':command+=['--model-deadline',str(DEADLINE)]
                command+=[script]
            with log.open('x')as stream:
                self.process=subprocess.Popen([*command,*map(str,args)],cwd=R,env=self.env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                if on_launch:on_launch(self.process.pid)
                try:return wait_bounded(self.process,cap,models,DEADLINE)
                finally:stop(self.process);self.process=None
        finally:
            if held is not None:held.close()
    def t0(self,t):
        self.set_task(t);name=f'v855_t0_slot{t["slot"]:02d}';pair=RAW/name/'paired'
        assert self.execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',120,'--max-steps',2400,'--initial-observation-steps',0,'--feasibility-only'],self.phase/(name+'.console'),125,True)==0,'T0_FAILED'
        assert self.execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],self.phase/(name+'_causal.console'),120)==0,'T0_CAUSAL_FAILED'
        self.pre.append(dict(task=t,run=str(pair.relative_to(R)),causal_audit=str((pair/'field_preflight/INITIAL_UNSEEN_AUDIT_V699.json').relative_to(R))));self.save()
    def unit(self,t,role,base=None):
        self.set_task(t);available=int(DEADLINE-time.time())-180
        if available<600:raise BudgetStop('LESS_THAN_TEN_MINUTES_FOR_NEW_NAVIGATION_AND_REPLAY')
        soft=min(5400,available);hard=soft+30;cap=hard+5;self.env['PHASE_NAV_SOFT_WALL_S']=str(soft)
        name=f'v855_{self.variant}_{role.lower()}_slot{t["slot"]:02d}';pair=RAW/name/'paired';row=dict(name=name,task=t,role=role,variant=self.variant,run=str(pair.relative_to(R)),base=None if base is None else base['run'],navigation_started=False,limits=dict(public_steps=2400,soft=soft,hard=hard,outer=cap,private_native=100000000),audits={},physical_passed=False,functional_passed=False);self.rows.append(row);self.save()
        def launched(pid):row.update(navigation_started=True,navigation_pid=pid,navigation_started_unix=time.time());self.save()
        code=self.execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',hard,'--max-steps',2400,'--initial-observation-steps',0],self.phase/(name+'.console'),cap,True,launched);row['runner_exit']=code
        row['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;row['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;self.save()
        if row['result']is not None or(row['interrupted']or{}).get('public_steps',0)>0:row['replay_exit']=self.execute('replay_native_audit.py',[pair],pair/'replay.console',120,True);self.save()
        assert code==0 and row['result']is not None,'MODEL_OR_EVIDENCE_EXCEPTION_NO_RETRY';assert row.get('replay_exit')==0,'FULL_NATIVE_REPLAY_FAILED'
        expected=read(ROOT/'QUALIFICATION.json')['expected_audit_statuses']
        for script,filename,cap in AUDITS:
            args=[pair]
            if script=='audit_run.py':args+=['--window',self.phase]
            if script=='audit_projection_learning.py':args+=['--model',R/'runs/v690_visible_eight_meter/training_8m/proposer.json']
            row['audits'][script]=self.execute(script,args,pair/(script+'.console'),cap,script=='audit_run.py');self.save();assert row['audits'][script]==0,(script,'FAILED')
            data=read(pair/filename);assert data['status']==expected[script]and all(data.get('checks',{}).values()),(script,'ASSERTION_FAILED')
        code=self.execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',300);chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');failed=[k for k,v in chain['checks'].items()if not v];assert not(set(failed)-FUNCTIONAL_CHECKS),'DISCOVERY_SAFETY_OR_CAUSAL_ANOMALY';assert(code==0)==(chain['status']=='PASS')
        row.update(physical_passed=True,functional_passed=chain['status']=='PASS'and row['result']['strict_safe_arrival'],functional_failed_checks=failed);self.save()
        if base is not None:
            repeated=compare(R/base['run'],pair);dump(pair/'EXACT_REPEAT_AUDIT.json',repeated);row['repeat_passed']=repeated['passed'];self.save();assert repeated['passed'],'FULL_REPEAT_MISMATCH'
        if not row['functional_passed']:raise FunctionalStop('SAFE_FUNCTIONAL_NOT_PASSED')
        return row
    def routes(self,pre):
        self.pre=pre;self.save();dump(self.phase/'LOCKED_T0_TASK_LIST.json',tasks());assert self.execute('audit_field_preflight.py',[self.phase],self.phase/'t0_aggregate.console',120)==0
        status='RUNNING'
        try:
            mains=[]
            for t in tasks():mains.append(self.unit(t,'MAIN'))
            for t,first in zip(tasks(),mains):self.unit(t,'REPEAT',first)
            assert complete_gate(self.rows);status='THREE_ROUTES_AND_FULL_REPEATS_PASS'
        except FunctionalStop:status='SAFE_FUNCTIONAL_NOT_PASSED'
        except BudgetStop:status='ABSOLUTE_BUDGET_STOP_UNEXECUTED_REMAINING'
        finally:
            self.save();dump(self.phase/'COMPLETION.json',dict(status=status,records=self.rows,planned_main=3,planned_repeat=3,new24=0,closed=True));v=read(self.phase/'ROUND_WINDOW.json');v.update(round_closed=True,status=status,closed_unix=time.time());dump(self.phase/'ROUND_WINDOW.json',v);dump(self.phase/'ACTIVE.json',dict(completed=True,status=status))
        return status
