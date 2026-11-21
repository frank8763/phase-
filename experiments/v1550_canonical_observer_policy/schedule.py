"""One original high-level request template, never old actuator controls.

No numerical imports or model permission. Gear holds consume these same ticks.
"""
import hashlib
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
TEMPLATE = 'runs/v1144_saved_entry_relay/software/ROWS.json'
TEMPLATE_SHA = '6fc261bfcd728d311d47617f275e42433e99db5e75d18d50f29bb817e76e89be'
CUT = 11400
STOP = 2200


def raw_rows(prepared_sources):
    path = R / TEMPLATE
    assert path.resolve() == path and not path.is_symlink()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == prepared_sources[TEMPLATE] == TEMPLATE_SHA
    source = json.loads(path.read_text())['rows']
    remaining = CUT
    answer = []
    for target, speed, count, parked in source:
        assert type(count) is int and count > 0
        assert type(parked) is int and parked in (0, 1)
        assert math.isfinite(target) and abs(target) <= .42722137342572125
        assert math.isfinite(speed) and speed in (0., -.03, .08, .12)
        assert not parked or speed == 0.
        take = min(remaining, count)
        if take:
            answer.append((float(target), float(speed), take, parked))
        remaining -= take
        if not remaining:
            break
    assert remaining == 0
    answer.append((0., 0., STOP, 0))
    assert sum(row[2] for row in answer) == 13600
    return tuple(answer)


def boundaries(rows):
    """Original zero/park full-row and moving min(8,remaining-row) cuts."""
    offset = 0
    answer = []
    for target, speed, count, parked in rows:
        remaining = count
        while remaining:
            take = remaining if parked or speed == 0. else min(8, remaining)
            answer.append((offset, take))
            offset += take
            remaining -= take
    assert offset == 13600 and len(answer) == 281
    return tuple(answer)


def at(rows, offset):
    assert type(offset) is int and 0 <= offset < 13600
    for target, speed, count, parked in rows:
        if offset < count:
            return (target, speed, parked)
        offset -= count
    raise AssertionError('ORIGINAL_REQUEST_OFFSET_OUTSIDE_FIXED_CATALOGUE0')


def body_request(raw):
    target, speed, parked = raw
    assert type(parked) is int and parked in (0, 1)
    assert math.isfinite(target) and math.isfinite(speed)
    assert abs(target) <= .42722137342572125
    assert speed in (0., -.03, .08, .12) and (not parked or speed == 0.)
    return float(speed), 0. if parked or speed == 0. else speed * math.tan(target) / .6


def metadata(prepared_sources):
    rows = raw_rows(prepared_sources)
    cuts = boundaries(rows)
    n = sum(row[2] for row in rows)
    witness = sum(2 * STOP + count for _, count in cuts)
    # Complete thirteen-array schema in evidence.py, dtype float64/int64.
    # 216 bytes for each N+1 state row, 168 bytes for each N action row.
    raw_bytes = lambda count: 216 * (count + 1) + 168 * count
    payload = raw_bytes(n) + sum(raw_bytes(STOP) + raw_bytes(count + STOP) for _, count in cuts)
    return dict(original_catalogue_index=0,stage_native=0,source_cut=CUT,
                nominal_native=n,boundaries=len(cuts),witness_native=witness,
                total_native_per_phase=n+witness,
                python_generation_explicit_Predictor=1,python_generation_deepcopies=2*len(cuts),
                independent_CPP_explicit_Engine=1,independent_CPP_carrier_copies=2*len(cuts),
                python_step_calls_upper=n+witness,CPP_simulate_one_step_calls_upper=n+witness,
                internal_Allocator_constructors=None,
                raw_thirteen_array_payload_per_phase_bytes=payload,
                raw_generation_and_audit_payload_bytes=2*payload,
                compressed_evidence_or_archive_peak_bound=None,complete_time_bound=None,
                opaque_geometry_math_init_work_unknown=True,
                no_selector_or_endpoint_pruning=True,models_authorized=False)
