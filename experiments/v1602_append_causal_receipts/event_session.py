"""Original event contract plus durable real-input provenance, no certificate."""
import importlib.util
from pathlib import Path
_s = importlib.util.spec_from_file_location('v1574_session_io', Path(__file__).with_name('source_io.py'))
io = importlib.util.module_from_spec(_s); _s.loader.exec_module(io)
old = io.exact('v1574_original_ordered_session', io.R / 'experiments/v1422_ordered_route_event/session.py')
Session = old.Session


def prepare_request(envelope, segment, geometry, tracker, **options):
    packet = old.prepare_request(envelope, segment, geometry, tracker, **options)
    source = tracker.event_source(envelope, packet['request'])
    assert source['snapshot'] == packet['causal_snapshot']
    packet['current_causal_source'] = source
    packet['current_causal_source_sha256'] = io.digest(source)
    return packet


def current_notice(notice, *, output, run_id, last_event_index):
    assert notice['kind'] == 'BRIDGE_CERTIFICATE_REQUEST_FILE' and notice['run_id'] == run_id
    assert type(notice['event_index']) is int and notice['event_index'] == last_event_index + 1
    expected = Path(output) / 'cusp_requests' / ('event%04d.json' % notice['event_index'])
    assert io.R / notice['path'] == expected
    packet = io.read_bound(expected, maximum=4 * 1024**2, expected_sha256=notice['file_sha256'])
    session = Session(packet); request = packet['request']
    assert request['run_id'] == run_id and request['event_index'] == notice['event_index']
    assert session.request_sha256 == notice['request_sha256']
    assert io.digest(packet['current_causal_source']) == packet['current_causal_source_sha256']
    assert packet['causal_snapshot'] == packet['current_causal_source']['snapshot']
    return packet
