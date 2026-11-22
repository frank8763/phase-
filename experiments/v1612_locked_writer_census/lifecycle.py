"""First current goal-bound event lifecycle seams; no round launcher here.

Actual authority must exist before factory binding. The initializer and final
state/Allocator/replay functions are the qualified originals. This class wires
current private/live components; it does not manufacture source/runtime PASS.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def exact(name,path,source):
    assert sha(path)==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def authorize(task,window):
    path=O/'ACTUAL_ADMISSION.json'
    assert path.is_file(),'GOAL_BOUND_ACTUAL_RUNTIME_NOT_ADMITTED'
    a=read(path);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert a['scope']=='REVISION12_FIRST_GOAL_BOUND_SEGMENT_ACTUAL_RUNTIME'
    assert a['scientific_revision']==parent['scientific_revisions']==12
    assert a['physical_authorized']and a['models_authorized']and not a['whole_route_admission']
    assert a['round_id']==parent['active_round']and parent['active_math_round']is None and parent['models_now_authorized']
    assert a['window']==window and a['boot_id']==window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert time.time()<a['execution_deadline_unix']<=window['absolute_deadline_unix']<=1795395600
    assert time.monotonic()<a['execution_deadline_monotonic']<=window['hard_stop_monotonic']<=parent['hard_stop_monotonic']
    assert 0<window['absolute_deadline_unix']-window['started_unix']<=5400
    assert task==read(O/'TASK.json')and task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
    assert task['nav2_params']==str(R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json')
    q=read(R/a['source_qualification_path']);assert q.get('complete_actual_source_target_passed') is True,'COMPLETE_ACTUAL_SOURCE_TARGET_NOT_QUALIFIED'
    assert q['passed']and q['closed']and q['models']==q['physical_native']==0
    freeze=R/a['source_freeze_path'];source=read(freeze)['files'];assert sha(freeze)==a['source_freeze_sha256']
    recovery=read(R/a['source_recovery_path'])
    assert recovery['passed']and recovery['source_freeze_sha256']==sha(freeze)
    assert recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
    assert all(sha(R/n)==h for n,h in source.items())
    assert (O/'ACTUAL_ONCE_CLAIM.json').is_file()
    assert sha(O/'ACTUAL_ONCE_CLAIM.json')==a['once_claim_sha256']
    if sorted(os.sched_getaffinity(0))==[2]:assert os.environ.get('PHASE_REPO')==str(R)
    else:assert sorted(os.sched_getaffinity(0))==[3]and a['ROS_authorized']
    return a,source


class Lifecycle:
    def __init__(self,*,task,window,lock,atomic,quota,check_budget):
        self.authority,self.source=authorize(task,window);self.task=copy.deepcopy(task);self.window=window
        self.output=Path(task['output']);self.lock=lock;self.atomic=atomic;self.quota=quota;self.check_budget=check_budget
        assert sorted(os.sched_getaffinity(0))==[2]
        assert Path('/proc/self/fd/%d'%lock.fileno()).resolve()==R/'runs/v648_static_unknown/execution.lock'
        rows=Path('/proc/self/fdinfo/%d'%lock.fileno()).read_text().splitlines()
        assert any(line.startswith('lock:')and 'FLOCK'in line and 'WRITE'in line and str(os.getpid())in line.split()for line in rows)
        self.canonical=None;self.components=None;self.private_claimed=False

    def bind_initialized_t0(self,vehicle,setup):
        assert self.canonical is None and vehicle.count==0 and float(vehicle.d.time)==0.
        module=exact('v1612_real_current_canonical_owner',C/'canonical_owner.py',self.source)
        self.canonical=module.create(vehicle,task=self.task,output=self.output,setup=setup,prepared_sources=self.source,
            atomic=self.atomic,check_budget=self.check_budget,quota=self.quota,lock=self.lock,
            private_admission=self.private_admission,install_live=self.install_live,prepare_stage=self.prepare_private_stage)
        return self.canonical

    def private_admission(self,*,method,stopped_source,output,lock):
        assert not self.private_claimed and lock is self.lock and stopped_source.native is self.canonical.native
        self.check_budget('PUMP',0);stopped_source.verify_stopped_source(method)
        self.quota.retire_grant()
        # All model outputs remain inside the224MiB root scope and are
        # pre-reserved before long preparation, never on a fresh command path.
        self.quota.prepare_grant(112*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,
            external_writers=self.quota.external_writers)
        self.private_claimed=True
        claim=output/'NUMERIC_ONCE_CLAIM.json'
        assert not claim.exists();self.atomic(claim,dict(round_id=self.authority['round_id'],current_input_sha256=method['response_method_sha256'],unix=time.time()))
        now=time.time();mono=time.monotonic();window=self.window
        value=dict(scope='REVISION12_SINGLE_GOAL_BOUND_CURRENT_EVENT_PRIVATE',scientific_revision=12,maximum_events=1,
            models_authorized=True,physical_authorized=False,replay_authorized=False,optimizer_authorized=False,whole_route_admission=False,
            round_id=self.authority['round_id'],started_unix=now,started_monotonic=mono,
            absolute_deadline_unix=window['absolute_deadline_unix'],hard_stop_monotonic=window['hard_stop_monotonic'],boot_id=window['boot_id'],
            source_freeze_path=self.authority['source_freeze_path'],source_freeze_sha256=self.authority['source_freeze_sha256'],
            source_recovery_path=self.authority['source_recovery_path'],source_qualification_path=self.authority['source_qualification_path'],
            once_claim_sha256=sha(claim),source_owner_path=str((C/'source_owner.py').relative_to(R)),
            complete_phase_native_cap=5300800,phase_seconds=dict(CPP_PROPOSAL=240,CPP_GENERATION=1800,PYTHON_AUDIT=1800),
            work_deadline_unix=self.authority['execution_deadline_unix'],work_deadline_monotonic=self.authority['execution_deadline_monotonic'],
            current_input_sha256=method['response_method_sha256'])
        self.atomic(output/'GOAL_BOUND_PRIVATE_ADMISSION.json',value)

    def prepare_private_stage(self,stage):
        assert stage in ('CPP_PROPOSAL','CPP_GENERATION','PYTHON_AUDIT')
        self.check_budget('PUMP',0)
        self.quota.retire_grant()
        self.quota.prepare_grant(40*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,
            external_writers=self.quota.external_writers)

    def install_live(self,*,context,canonical_owner):
        assert canonical_owner is self.canonical and self.components is None
        context['source_owner'].verify_stopped_source(context['method']);self.check_budget('PUMP',0)
        self.quota.retire_grant()
        self.quota.prepare_grant(40*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=1800,
            external_writers=self.quota.external_writers)
        folder=self.output/'goal_bound_actual';folder.mkdir(exist_ok=False)
        budgets=exact('v1612_actual_original_writer',R/'experiments/v1436_pathlib_control_rename/writer_budget.py',self.source)
        io=exact('v1612_actual_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py',self.source)
        components=exact('v1612_same_current_live_components',C/'components.py',self.source)
        scopes=exact('v1612_composed_current_writer',C/'scoped_output.py',self.source)
        scope=scopes.Scope(parent=self.quota.output_boundary,folder=folder,writers=budgets,io=io,maximum_bytes=32*1024**2,source_identity=digest(self.source))
        writer=scope.writer
        with scope.activate()as boundary:
            self.components=components.Components(context=context,native=canonical_owner.native,actual_admission=O/'ACTUAL_ADMISSION.json',
                output=folder,writer=writer,boundary=boundary,scope=scope,source=self.source,check_budget=self.check_budget)
        # Retire the stopped preparation grant before obtaining the next real
        # wire; Pump prepares its original short grant at the5native boundary.
        self.quota.retire_grant()
        return self.components.install()

    def close(self):
        if self.components is not None:self.components.close()
        if self.canonical is not None:self.canonical.close()


def run(task,window):
    # The actual native initializer/close/audit supervisor must invoke the
    # explicit Lifecycle seam. No inherited scope can enter an old owner.
    _,source=authorize(task,window)
    module=exact('v1612_explicit_native_initializer_closure',C/'native_driver.py',source)
    return module.run(task,window)
