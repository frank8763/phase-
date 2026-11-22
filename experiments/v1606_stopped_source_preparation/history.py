"""Full stopped historical content preparation, no fresh/model/live authority.

Draft only. The final current transaction and production handshake are not
integrated or qualified. No old source timestamp is changed by this module.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def stopped_identity(native,capture):
    assert not native.in_step and not native.bridge_started
    v=native.vehicle;tick=v.count
    assert tick==native.applied==len(v.commands)==len(v.rows)==len(native.events)==v.audit.native_count
    assert len(v.contacts)==tick+1 and v.bad==0 and native.gear.last_tick==tick-1
    assert max(abs(x)for x in v.body()[3:])<=.003
    assert max(abs(x)for x in v.steering_sample()[2:])<=.03
    assert max(abs(x)for x in v.adapter.last[2:])<=1e-10
    return dict(native=tick,fullstate=capture.fullstate(v),mode=native.mode_memory.snapshot(tick),
        gear=dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start),
        last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral))

class PreparedHistory:
    def __init__(self,*,native,output,packet,source,save):
        self.native=native;self.output=Path(output).resolve();self.source=source.copy()
        self.capture=exact('v1606_original_complete_history',BASE/'capture.py',source)
        self.provider=exact('v1606_original_complete_causal_reader',BASE/'causal_provider.py',source)
        self.poisoned=True;self.refresh_consumed=False
        assert self.output.is_relative_to(R/'runs')
        before=stopped_identity(native,self.capture)
        request=packet['request'];origin=packet['current_causal_source']
        assert request['actual']['evidence_state_sha256']==digest(before['fullstate'])
        assert origin['snapshot']==packet['causal_snapshot']
        wire=request['actual']['wire']
        # This historical preparation deliberately grants no freshness. The
        # subsequent transaction must sample and bind a new real current wire.
        history=self.capture.prefix_coverage(native,self.output)
        causal=self.provider.verify(origin,native,wire,request,prepared_sources=source,output=self.output)
        assert stopped_identity(native,self.capture)==before
        self.identity=copy.deepcopy(before);self.packet=copy.deepcopy(packet)
        self.refs=copy.deepcopy(origin['observation_receipts'])
        self.prefix=copy.deepcopy(origin['observation_journal'])
        self.head=origin['receipt_head_sha256'];self.sequence=wire['sequence']
        self.novel=causal['novel_records'];self.gaps=causal['skipped_published_sequences']
        self.proof=dict(passed=True,role='STOPPED_HISTORY_PREPARATION_NOT_CURRENT_CAPTURE',
            stopped_identity_sha256=digest(before),original_request_sha256=request['request_sha256'],
            complete_applied_history=history,complete_causal_history=causal,
            original_causal_prefix=copy.deepcopy(self.prefix),original_wire_sha256=digest(wire),
            numerical_permission=False,physical_permission=False,current_capture_passed=False)
        save(self.proof)
        self.proof_sha256=digest(self.proof);self.poisoned=False

    def same_stopped_state(self):
        assert not self.poisoned
        assert stopped_identity(self.native,self.capture)==self.identity,'STOPPED_HISTORY_CURRENT_STATE_CHANGED'
        return True

    def extended_causal_content(self,origin,wire,request):
        """Read immutable old prefix bytes, parse and bind every appended row.

        This helper does not grant freshness or capture PASS. A new current
        capture must still run all original current fields and both age gates.
        """
        assert not self.poisoned
        self.poisoned=True
        n=self.native;self.same_stopped_state_unchecked()
        assert origin['run_id']==wire['run_id']==n.run_id
        assert origin['covered_native']==wire['native_tick']==n.vehicle.count
        assert n.sent[wire['sequence']]==wire and wire['sequence']>self.sequence
        assert origin['request_sha256']==request['request_sha256']
        assert origin['observation_wire_sha256']==digest(wire)
        assert origin['online_actor_truth']is False and origin['all_published_scans_observed']is False
        refs=origin['observation_receipts'];count=len(self.refs)
        assert count<len(refs)==origin['received_observations']<=12001
        assert refs[:count]==self.refs and storage_identity(origin['observation_journal'])==storage_identity(self.prefix)
        storage=origin['observation_journal'];assert storage['records']==len(refs)
        raw=self.provider.journal.read_prefix(self.output,storage)
        offset=self.prefix['prefix_bytes']
        assert hashlib.sha256(raw[:offset]).hexdigest()==self.prefix['prefix_sha256']
        head=self.head;last=self.sequence;updates=self.novel;gaps=self.gaps
        for index,ref in enumerate(refs[count:],start=count):
            row,offset=self.provider.journal.row_at(raw,ref,path=storage['path'],offset=offset)
            observed=row['wire'];seq=observed['sequence']
            assert row['index']==index and row['previous_sha256']==head and row['run_id']==n.run_id
            assert row['role']=='ACTUAL_WIRE_TO_ORIGINAL_CAUSAL_TRACKER'and row['online_actor_truth']is False
            assert type(seq)is int and last<seq<=wire['sequence']and observed==n.sent[seq]
            assert digest(observed)==row['wire_sha256']and row['prior_sequence']==last
            assert row['skipped_published_sequences']==seq-last-1
            assert row['observation_records_before']==updates
            records=row['new_observation_records'];updates+=len(records)
            assert row['observation_records_after']==updates
            assert all(r['native_tick']==observed['native_tick']and r['sim_time']==observed['sim_time']
                and r['range']==observed['ranges_m'][r['ray']]for r in records)
            gaps+=seq-last-1;last=seq;head=digest(row)
        assert offset==len(raw)==storage['prefix_bytes']and last==wire['sequence']
        assert head==origin['receipt_head_sha256']
        snapshot=origin['snapshot']
        assert snapshot['online_actor_truth']is False and snapshot['model']=='PERIODIC'
        assert snapshot['forecast_kind']in ('HORIZON','NESTED_SWEEP')
        assert digest(snapshot)==origin['snapshot_sha256']==request['causal_forecast']['coefficient_snapshot_sha256']
        assert snapshot['periodic']['source_tick']==request['event']['source']['coefficient_tick']<=wire['native_tick']
        for key in ('provider_definition','update_definition','known_static_definition','storage_provider_definition','journal_definition'):
            assert origin[key]==self.packet['current_causal_source'][key]
        self.same_stopped_state_unchecked();self.poisoned=False
        return dict(received_inputs=len(refs),prepared_inputs=count,new_inputs=len(refs)-count,
            novel_records=updates,skipped_published_sequences=gaps,receipt_head_sha256=head,
            complete_prepared_prefix_SHA_rechecked=True,all_new_inputs_bound_to_actual_sent_wires=True,all_recorded_inputs_bound_to_actual_sent_wires=True,
            estimator_recomputed=False,current_capture_passed=False,numerical_permission=False,physical_permission=False)

    def same_stopped_state_unchecked(self):
        assert stopped_identity(self.native,self.capture)==self.identity,'STOPPED_PREPARATION_STATE_CHANGED'

def storage_identity(value):
    return value['storage_kind'],value['path']
