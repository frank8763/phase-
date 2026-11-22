"""Record real tracker inputs without changing its estimator or observations.

No tracker construction on import. The existing ROS process supplies its one
original tracker, and every update goes through observe(). No actor truth API.
Runtime/source coverage remains unqualified until a new bounded target runs.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path

_s = importlib.util.spec_from_file_location('v1574_source_bytes', Path(__file__).with_name('source_io.py'))
io = importlib.util.module_from_spec(_s); _s.loader.exec_module(io)
TRACKER = 'experiments/v1370_overnight_controller_matrix/causal_occupancy.py'
UPDATE = 'experiments/v1357_expiry_evidence_relay/causal_occupancy.py'
KNOWN = 'experiments/v855_renewal_worker/KNOWN_FIELD.json'


class ObservedTracker:
    def __init__(self, tracker, *, run_id, output, save):
        assert Path(type(tracker).snapshot.__code__.co_filename).resolve() == io.R / TRACKER
        assert Path(type(tracker).update.__code__.co_filename).resolve() == io.R / UPDATE
        assert tracker.last_tick == -1 and not tracker.records, 'TRACKER_REQUIRES_EMPTY_REAL_HISTORY'
        import json
        assert tracker.known == json.loads((io.R / KNOWN).read_text()), 'PUBLIC_STATIC_FIELD_CHANGED'
        self._tracker = tracker
        self.run_id = run_id; self.output = Path(output).resolve(); self.save = save
        assert self.output.is_relative_to(io.R / 'runs')
        self.receipts = []; self.head = None; self.last_sequence = -1; self.poisoned = False

    def observe(self, wire):
        assert not self.poisoned
        self.poisoned = True  # save/update failure is terminal; never retry a consumed input.
        assert wire['run_id'] == self.run_id and type(wire['sequence']) is int
        assert wire['sequence'] > self.last_sequence
        before = copy.deepcopy(self._tracker.snapshot())
        old_count = len(self._tracker.records)
        seen = self._tracker.update(native_tick=wire['native_tick'], sim_time=wire['sim_time'],
                                    center_body=wire['body'], ranges=wire['ranges_m'])
        after = copy.deepcopy(self._tracker.snapshot())
        row = dict(role='ACTUAL_WIRE_TO_ORIGINAL_CAUSAL_TRACKER', run_id=self.run_id,
                   index=len(self.receipts), previous_sha256=self.head,
                   wire=copy.deepcopy(wire), wire_sha256=io.digest(wire),
                   before_snapshot_sha256=io.digest(before), after_snapshot_sha256=io.digest(after),
                   observation_records_before=old_count, observation_records_after=len(self._tracker.records),
                   novel_return=bool(seen), new_observation_records=copy.deepcopy(self._tracker.records[old_count:]),
                   prior_sequence=self.last_sequence,
                   skipped_published_sequences=wire['sequence'] - self.last_sequence - 1,
                   online_actor_truth=False)
        identity = io.digest(row)
        path = self.output / 'causal_source' / ('observation%05d.json' % len(self.receipts))
        assert len(self.receipts) < 12001 and not path.exists(), 'CAUSAL_RECEIPT_COUNT_OR_DUPLICATE'
        # Outer OutputBoundary charges every write. save must be atomic+fsync;
        # no post-write claimed success is published if durability fails.
        self.save(path, row)
        data=path.read_bytes()
        assert len(data)<=16384 and __import__('json').loads(data)==row, 'CAUSAL_RECEIPT_READBACK'
        self.receipts.append(dict(path=str(path.relative_to(io.R)), semantic_sha256=identity,
                                  file_sha256=hashlib.sha256(data).hexdigest(),file_size=len(data)))
        self.head = identity; self.last_sequence = wire['sequence']; self.poisoned = False
        return seen

    def event_source(self, envelope, request):
        assert not self.poisoned and self.receipts
        wire = envelope['wire']; snapshot = copy.deepcopy(self._tracker.snapshot())
        assert wire['sequence'] == self.last_sequence and wire['native_tick'] == self._tracker.last_tick
        assert io.digest(snapshot) == request['causal_forecast']['coefficient_snapshot_sha256']
        return dict(role='CURRENT_CANONICAL_OBSERVATION_CAUSAL_SOURCE', run_id=self.run_id,
                    covered_native=wire['native_tick'], observation_wire_sha256=io.digest(wire),
                    request_sha256=request['request_sha256'], snapshot=snapshot,
                    snapshot_sha256=io.digest(snapshot), receipt_head_sha256=self.head,
                    observation_receipts=copy.deepcopy(self.receipts), received_observations=len(self.receipts),
                    all_published_scans_observed=False, online_actor_truth=False,
                    provider_definition=TRACKER, update_definition=UPDATE, known_static_definition=KNOWN,
                    content_provider_runtime_qualified=False, numerical_permission=False, physical_permission=False)

    # Original raster/occupied_ball may append its own sweep/forecast metadata.
    # event_source binds the actual final snapshot, rather than incorrectly
    # assuming it is byte-identical to the last update snapshot.
    def snapshot(self): return copy.deepcopy(self._tracker.snapshot())
    def occupied_ball(self, sim_time): return self._tracker.occupied_ball(sim_time)
    def raster(self, grid, sim_time): return self._tracker.raster(grid, sim_time)
    @property
    def records(self): return self._tracker.records
    @property
    def forecasts(self): return self._tracker.forecasts


def verify(source, native, wire, request, *, prepared_sources, output):
    """Read actual receipt content, cross-bind each input to native sent wires.

    This proves recorded input/source identity, not estimator correctness,
    unobserved scan coverage, method acceptance or live runtime qualification.
    """
    assert source['role'] == 'CURRENT_CANONICAL_OBSERVATION_CAUSAL_SOURCE'
    assert source['run_id'] == native.run_id == wire['run_id']
    assert source['covered_native'] == wire['native_tick'] == native.vehicle.count
    assert source['observation_wire_sha256'] == io.digest(wire)
    assert source['request_sha256'] == request['request_sha256']
    assert source['online_actor_truth'] is False and source['all_published_scans_observed'] is False
    snapshot = source['snapshot']
    assert snapshot['online_actor_truth'] is False
    assert snapshot['model'] == 'PERIODIC' and snapshot['forecast_kind'] in ('HORIZON', 'NESTED_SWEEP')
    assert io.digest(snapshot) == source['snapshot_sha256'] == request['causal_forecast']['coefficient_snapshot_sha256']
    assert snapshot['periodic']['source_tick'] == request['event']['source']['coefficient_tick'] <= wire['native_tick']
    for key, path in [('provider_definition', TRACKER), ('update_definition', UPDATE), ('known_static_definition', KNOWN)]:
        assert source[key] == path and path in prepared_sources
    refs = source['observation_receipts']; head = None; last = -1; updates = 0; gaps = 0
    assert 0 < len(refs) == source['received_observations'] <= 12001
    for index, ref in enumerate(refs):
        path = io.R / ref['path']; expected = Path(output) / 'causal_source' / ('observation%05d.json' % index)
        assert path == expected and path.resolve() == expected and not path.is_symlink()
        assert path.stat().st_size == ref['file_size'] <= 16384
        row=io.read_bound(path,maximum=16384,expected_sha256=ref['file_sha256'])
        assert io.digest(row) == ref['semantic_sha256']
        assert row['role'] == 'ACTUAL_WIRE_TO_ORIGINAL_CAUSAL_TRACKER' and row['run_id'] == native.run_id
        assert row['index'] == index and row['previous_sha256'] == head
        observed = row['wire']; sequence = observed['sequence']
        assert type(sequence) is int and last < sequence <= wire['sequence']
        assert observed == native.sent[sequence] and io.digest(observed) == row['wire_sha256']
        assert row['prior_sequence'] == last and row['skipped_published_sequences'] == sequence - last - 1
        assert row['observation_records_before'] == updates
        records = row['new_observation_records']; updates += len(records)
        assert row['observation_records_after'] == updates and row['online_actor_truth'] is False
        assert all(r['native_tick'] == observed['native_tick'] and r['sim_time'] == observed['sim_time']
                   and r['range'] == observed['ranges_m'][r['ray']] for r in records)
        gaps += row['skipped_published_sequences']; last = sequence; head = io.digest(row)
    assert head == source['receipt_head_sha256'] and last == wire['sequence']
    return dict(received_inputs=len(refs), novel_records=updates, skipped_published_sequences=gaps,
                receipt_head_sha256=head, all_recorded_inputs_bound_to_actual_sent_wires=True,
                complete_sensor_coverage_claim=False, estimator_recomputed=False,
                provider_runtime_qualified=False, models_authorized=False)
