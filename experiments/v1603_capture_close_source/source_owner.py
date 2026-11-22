"""Read the stopped canonical source; no new scan, plant step or epoch reset.

Initial capture's200ms gate remains in V1574. Long private preparation retains
that source clock and rechecks the unchanged stopped plant. Later execution
must obtain a NEW wire and apply the original post-certificate200ms gate.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class StoppedSource:
    def __init__(self,*,canonical_owner,capture,proof,request,prepared_sources,output,setup):
        self.native=canonical_owner.native;self.output=Path(output).resolve();self.setup=copy.deepcopy(setup)
        assert self.output.is_relative_to(R/'runs')
        self.source=prepared_sources.copy();self.capture=copy.deepcopy(capture)
        self.proof=copy.deepcopy(proof);self.request=copy.deepcopy(request);self.poisoned=False
        p=C/'capture.py'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==self.source[str(p.relative_to(R))]
        s=importlib.util.spec_from_file_location('v1603_exact_current_source_content',p)
        self.module=importlib.util.module_from_spec(s);s.loader.exec_module(self.module)
        assert proof['passed']and proof['source_only']and proof['first_error']is None
        assert digest(capture['packet'])==proof['current_packet_sha256']
        assert capture['fullstate']==proof['before_fullstate']
        self.capture_sha=digest(capture);self.proof_sha=digest(proof)

    def verify_stopped_source(self,method):
        assert not self.poisoned
        try:
            n=self.native;v=n.vehicle;source=method['base_method']['physical_source']
            assert Path(type(n).packet.__code__.co_filename).resolve()==R/'experiments/v1567_epoch_scope_target/native_step.py'
            assert not n.in_step and not n.bridge_started
            assert v.count==n.applied==method['base_method']['fixed_origin_native']
            assert source['complete_capture_sha256']==self.capture_sha
            assert method['capture_proof_sha256']==self.proof_sha
            assert source['packet']==self.capture['packet']and source['fullstate']==self.capture['fullstate']
            assert self.module.fullstate(v)==source['fullstate'],'STOPPED_SOURCE_FULLSTATE_CHANGED'
            assert n.mode_memory.snapshot(v.count)==source['mode_history']
            assert dict(gear=n.gear.gear,last_tick=n.gear.last_tick,brake_start=n.gear.brake_start)==source['gear_memory']
            assert len(v.commands)==len(v.rows)==len(n.events)==v.audit.native_count==v.count
            assert len(v.contacts)==v.count+1 and v.bad==0
            packet=source['packet'];assert v.adapter.last.tolist()==packet['controller_memory']['last_ctrl']
            assert float(v.adapter.integral)==packet['controller_memory']['integral']
            assert v.steering_sample().tolist()==[*packet['steering']['position'],*packet['steering']['velocity']]
            assert list(v.body())==packet['body']and float(v.d.time)==packet['sim_time']
            assert max(abs(x)for x in packet['body'][3:])<=.003
            assert max(abs(x)for x in packet['steering']['velocity'])<=.03
            wire=self.request['actual']['wire']
            assert wire==n.sent[wire['sequence']]
            assert source['causal_snapshot']==self.capture['causal_source']['snapshot']
            assert digest(source['causal_snapshot'])==method['causal_snapshot_sha256']
            assert self.request['next_segment']==method['actual_next_segment']
            self.module.prefix_coverage(n,self.output)
            self.module.provider.verify(self.capture['causal_source'],n,wire,self.request,
                prepared_sources=self.source,output=self.output)
            return True
        except BaseException:
            self.poisoned=True;raise
