"""Necessary new resource seam; no old suite or numerical work."""
import ast
import copy
import fcntl
from pathlib import Path
import select
import subprocess
import sys
import time

def run(c,source,target,save,refused,writer,io):
    old=c.R/'experiments/v1609_complete_refresh_source'
    changed={'base_quota.py','supervisor.py','common.py','entry.py','source_target.py','source_owner_entry.py'}
    reused=[]
    for p in old.glob('*.py'):
        if p.name in changed:continue
        current=c.C/p.name
        normalized=current.read_text().replace(c.C.name,old.name).replace('v1615','v1609')
        assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(p.read_text())),p.name
        reused.append(dict(name=p.name,old_sha256=c.sha(p),new_sha256=c.sha(current)))
    before=ast.parse((old/'supervisor.py').read_text())
    after=ast.parse((c.C/'supervisor.py').read_text().replace(c.C.name,old.name).replace('v1615','v1609'))
    launch=next(n for n in after.body if isinstance(n,ast.FunctionDef)and n.name=='launch')
    stage=next(n for n in launch.body if isinstance(n,ast.Try))
    added=[n for n in stage.body if isinstance(n,ast.For)and ast.unparse(n.target)=='(role, cap)']
    assert len(added)==1 and 'writers.WriterBudget' in ast.unparse(added[0])
    stage.body.remove(added[0]);assert ast.dump(before)==ast.dump(after),'SUPERVISOR_OTHER_LOGIC_CHANGED'
    census=c.load('v1615_actual_counter_census',c.C/'census.py')
    base=c.load('v1615_actual_base_quota',c.C/'base_quota.py')
    wm=c.load('v1615_original_counter',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
    limits=c.read(c.C/'LIMITS.json');folder=target/'SOFTWARE_COUNTERS';folder.mkdir()
    identity=c.digest(source)
    registry=dict(source_identity=identity,writers={role:dict(maximum_bytes=cap,source_hook_coverage_qualified=True)for role,cap in census.CAPS.items()})
    # This trusted bootstrap has a prepaid finite metadata bound at the root.
    # It is exactly the original counter constructor, not a writable-FD escape.
    writer.reserve(folder/'SOFTWARE_COUNTER_BOOTSTRAP',256*1024)
    for role,cap in sorted(census.CAPS.items()):
        wm.WriterBudget(folder,role=role,maximum_bytes=cap,source_identity=identity)
    c.put(folder/'EXTERNAL_WRITER_RESERVATIONS.json',registry)
    children=[]
    def line(job,expected):
        assert select.select([job.stdout],[],[],2)[0],'COUNTER_WORKER_HANDSHAKE_TIMEOUT'
        actual=job.stdout.readline().decode().strip();assert actual==expected,(expected,actual)
    def worker(mode):
        job=subprocess.Popen([sys.executable,'-B',str(c.C/'census_worker.py'),str(folder),identity,mode],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        children.append(job);line(job,'READY');return job
    def command(job,text):job.stdin.write((text+'\n').encode());job.stdin.flush()
    def finish(job):
        line(job,'DONE');assert job.wait(timeout=2)==0
        assert job.stderr.read()==b''
        job.stdin.close();job.stdout.close();job.stderr.close()
    proof={}
    try:
        # A deterministic narrow TOCTOU witness, not a new actual du run or
        # physical sample: original _put pauses after writing .pending.
        red=worker('RED');command(red,'GO');line(red,'ATTEMPT');line(red,'PENDING')
        pending=folder/'WRITER_ACTUAL_ROS_BYTES.json.pending'
        observed=[p.name for p in folder.iterdir()];assert pending.name in observed
        command(red,'RENAME');finish(red)
        try:pending.lstat()
        except FileNotFoundError:proof['enumerated_counter_then_rename_stat_ENOENT']=True
        else:raise AssertionError('NARROW_ORIGINAL_COUNTER_RACE_NOT_REPRODUCED')
        # New production census uses the original real counter process, with
        # GNU du unchanged and every file included in both allocation scans.
        green=worker('GREEN');calls=[]
        def measured(path):
            if not calls:
                command(green,'GO');line(green,'ATTEMPT')
                assert not select.select([green.stdout],[],[],.03)[0],'EXCLUSIVE_COUNTER_WRITE_BYPASSED_SHARED_CENSUS_LOCK'
                assert green.poll()is None and not pending.exists()
            calls.append(str(path));return base.used(path)
        values=census.measure(folder,limits,measured);finish(green)
        assert len(calls)==2 and values[0]>0 and values[1]>=values[0]
        stable=census.measure(folder,limits,base.used)
        assert stable[0]==base.used(folder)
        proof.update(original_counter_blocked_during_real_du=True,writer_completed_after_census_release=True,all_files_counted_no_exclusions=True,stable_own_allocation_matches_du=True,own_allocated_bytes=stable[0],allruns_snapshot_bytes=stable[1],GNU_du_failures_retried=0)
        with io.OutputBoundary(target,writer.reserve):
            save(target/'COUNTER_RACE_AND_LOCK_PROOF.json',dict(passed=True,SOFTWARE=True,proof=proof,original_actual_failure_evidence='runs/v1609_complete_refresh_source/CURRENT_EVENT_DIAGNOSIS.json',models=0,actual_runtime_qualified=False))
            bad=copy.deepcopy(registry);bad['writers']['ACTUAL_ROS']['maximum_bytes']+=1
            c.put(folder/'EXTERNAL_WRITER_RESERVATIONS.json',bad)
            refused('role_cap_tamper',lambda:census.measure(folder,limits,base.used))
            bad=copy.deepcopy(registry);bad['writers']['ACTUAL_ROS']['source_hook_coverage_qualified']=False
            c.put(folder/'EXTERNAL_WRITER_RESERVATIONS.json',bad)
            refused('source_unqualified',lambda:census.measure(folder,limits,base.used))
            bad=copy.deepcopy(registry);bad['source_identity']='f'*64
            c.put(folder/'EXTERNAL_WRITER_RESERVATIONS.json',bad)
            refused('counter_source_identity_tamper',lambda:census.measure(folder,limits,base.used))
            c.put(folder/'EXTERNAL_WRITER_RESERVATIONS.json',registry)
            lock=folder/'WRITER_ACTUAL_ROS_BYTES.lock';moved=lock.with_suffix('.held')
            lock.replace(moved)
            refused('missing_initialized_counter_lock',lambda:census.measure(folder,limits,base.used))
            moved.replace(lock)
            with lock.open('rb')as exclusive:
                fcntl.flock(exclusive,fcntl.LOCK_EX)
                refused('counter_lock_deadline',lambda:census.measure(folder,limits,base.used))
            # Real GNU du error is propagated, never reclassified or retried.
            refused('unrelated_du_ENOENT',lambda:census.measure(folder,limits,lambda path:base.used(folder/'UNREGISTERED_MISSING_PAYLOAD')))
            def denied(path):raise PermissionError('SOFTWARE_UNRELATED_EACCES')
            refused('unrelated_measurement_EACCES',lambda:census.measure(folder,limits,denied))
            # Base admit and error_atomic must use the exact same census seam.
            quota=base.EvidenceQuota(folder,limits);admission=quota.admit(0,'SOFTWARE_NEW_CENSUS_SEAM')
            assert admission['task_allocated_bytes']==base.used(folder)
            quota.error_atomic(folder/'SOFTWARE_ERROR_SAVED.json',dict(SOFTWARE=True,error='EXPECTED'),lambda p,v:c.put(p,v))
            save(target/'COUNTER_SOURCE_REUSE.json',dict(passed=True,normalized_AST_reused=reused,supervisor_only_added_original_counter_preinit=True,old_suites_rerun=False,source_only=True))
        return dict(counter_race_and_shared_lock_proof=proof,numerical_source_modules_reused=len(reused),actual_capture_qualified=False,models=0,physical_native=0)
    finally:
        for job in children:
            if job.poll()is None:
                job.terminate()
                try:job.wait(timeout=2)
                except subprocess.TimeoutExpired:job.kill();job.wait(timeout=2)
