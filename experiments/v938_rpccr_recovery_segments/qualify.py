"""Fixed four saved states and adverse transaction cases; zero vehicle models."""
import copy
import hashlib
import importlib.abc
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).parent
OUT = ROOT/'runs/v938_rpccr_recovery_segments'
SAVED = ROOT/'runs/v936_rpccr_corridor_search'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'factory', 'physical', 'vehicle', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(CODE))
from independent_geometry import audit
from recovery import construct
from transaction import RecoveryTransaction, fingerprint


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    inputs = [SAVED/'ENTRY_QUALIFICATION.json', SAVED/'saved/SETUP.json']
    inputs += [SAVED/f'CASE_{target}.json' for target in [7000, 11000, 17000]]
    files = sorted(CODE.glob('*.py'))+[CODE/'PROTOCOL.md']+inputs
    files += [ROOT/'experiments/v936_rpccr_corridor_search/corridor_search.py',
              ROOT/'experiments/v936_rpccr_corridor_search/reference_loss.py',
              ROOT/'experiments/v884_feasible_rpp/A_feasible.yaml']
    frozen = {str(p.relative_to(ROOT)): sha(p) for p in files}
    (OUT/'SOURCE_FREEZE.json').write_text(json.dumps(dict(at=time.time(), files=frozen,
                                                       models=0, integrations=0), indent=2)+'\n')
    entry = load(inputs[0]); assert entry['passed']
    known = load(inputs[1])['known']
    first = entry['first_actual_trigger']
    cases = [dict(label='first_trigger_4947', packet=first['packet'], source=first['source'])]
    for target in [7000, 11000, 17000]:
        row = load(SAVED/f'CASE_{target}.json')
        cases.append(dict(label=f'fixed_{row["actual_body_tick"]}',
                          packet=row['actual_packet'], source=row['original_source']))
    results = []
    for case in cases:
        begun = time.monotonic()
        proposal = construct(case['packet']['body'][:3], [4., -2.], known, case['source']['periodic'])
        checked = audit(proposal['path'], known, case['source']['periodic']) if proposal['passed'] else dict(passed=False)
        results.append(dict(label=case['label'], body_tick=case['packet']['native_tick'],
                            source_tick=case['source']['source_native_tick'], proposal=proposal,
                            independent_audit=checked, total_qualification_wall_s=time.monotonic()-begun))
        print(json.dumps(dict(label=case['label'], proposed=proposal['passed'],
                              independent=checked['passed'],
                              progress_m=proposal.get('nominal_goal_progress_m'),
                              static_lower_m=checked.get('static_lower_m'),
                              dynamic_lower_m=checked.get('dynamic_cycle_lower_m'))), flush=True)
    (OUT/'CORRIDORS.json').write_text(json.dumps(results, indent=2)+'\n')
    checks = dict(original_actual_reference_loss_entry_passed=entry['passed'])
    checks['all_four_connected_progress_segments_independently_certified'] = all(
        row['proposal']['passed'] and row['independent_audit']['passed'] for row in results)
    assert checks['all_four_connected_progress_segments_independently_certified']
    proposal = results[0]['proposal']
    packet, source = first['packet'], first['source']
    now = packet['body_measured_at']

    def transaction(stage):
        m = RecoveryTransaction([4., -2.], known)
        m.request(packet, source, now)
        if stage >= 1: m.canceled(True)
        if stage >= 2: m.install(proposal, packet, source, now)
        if stage >= 3: m.accepted(True)
        if stage >= 4: m.follow_completed(4)
        return m

    m = transaction(3)
    expected = fingerprint(proposal['path'])
    checks['actual_stall_enters_explicit_cancel_transaction'] = m.events[0]['action']=='CANCEL_NORMAL_NAVIGATION'
    checks['one_exact_reference_for_original_rpp'] = sum(e['action']=='SEND_FOLLOW_PATH_ONCE' for e in m.events)==1 and m.path_sha256==expected
    checks['normal_periodic_replan_cannot_overwrite_segment'] = all(
        m.periodic_normal_plan()['action']=='IGNORE_PERIODIC_REFERENCE_OVERWRITE' for _ in range(5)) and m.path_sha256==expected
    checks['partial_segment_is_not_goal_success'] = proposal['goal_reached'] is False and proposal['nominal_terminal_goal_error_m']>.45
    # Synthetic callback fixtures test the transaction only, never measured movement.
    p = copy.deepcopy(packet); p['body']=[*proposal['path'][-1], 0., 0.]
    m.follow_completed(4)
    answer = m.finish_segment(p, source, now)
    checks['synthetic_completion_requests_original_goal_without_false_success'] = answer['goal']==[4., -2.] and answer['original_goal_success'] is False
    events = copy.deepcopy(m.events)

    def rejects(label, stage, invoke):
        m = transaction(stage)
        try:
            invoke(m)
        except (AssertionError, ValueError, KeyError):
            checks[label] = m.mode=='FAILED' and m.events[-1]['action']=='STOP_AND_CANCEL_ALL_ACTIONS'
        else:
            checks[label] = m.mode=='FAILED'

    def changed_packet(**values):
        p = copy.deepcopy(packet); p.update(values); return p

    rejects('install_before_cancel_ack_rejected', 0, lambda m:m.install(proposal, packet, source, now))
    rejects('duplicate_install_rejected', 2, lambda m:m.install(proposal, packet, source, now))
    rejects('moving_body_blocks_handoff', 1, lambda m:m.install(proposal, changed_packet(body=[*packet['body'][:3], .04, 0.]), source, now))
    rejects('stale_body_blocks_handoff', 1, lambda m:m.install(proposal, packet, source, now+.051))
    stale = copy.deepcopy(source); stale['source_age_s']=.201
    rejects('stale_scan_blocks_handoff', 1, lambda m:m.install(proposal, packet, stale, now))
    future = copy.deepcopy(source); future['source_native_tick']=packet['native_tick']+1
    rejects('future_source_blocks_handoff', 1, lambda m:m.install(proposal, packet, future, now))
    drift = changed_packet(body=[packet['body'][0]+.02, *packet['body'][1:]])
    rejects('body_drift_requires_reconstruction', 1, lambda m:m.install(proposal, drift, source, now))
    bad = copy.deepcopy(proposal); bad['path'][2][1]+=.1
    rejects('tampered_reference_blocks_handoff', 1, lambda m:m.install(bad, packet, source, now))
    rejected = copy.deepcopy(proposal); rejected['passed']=False
    rejects('unqualified_search_blocks_handoff', 1, lambda m:m.install(rejected, packet, source, now))
    wrong_goal = copy.deepcopy(proposal); wrong_goal['original_goal']=[1., 1.]
    rejects('goal_replacement_rejected', 1, lambda m:m.install(wrong_goal, packet, source, now))
    enlarged = copy.deepcopy(source)
    for vertices in enlarged['periodic']['vertices']:
        for v in vertices: v[0]=0.
    rejects('current_changed_risk_set_revalidated', 1, lambda m:m.install(proposal, packet, enlarged, now))
    rejects('cancel_rejection_stops', 0, lambda m:m.canceled(False))
    rejects('rpp_rejection_stops', 2, lambda m:m.accepted(False))
    rejects('failed_rpp_action_stops', 3, lambda m:m.follow_completed(6))
    rejects('action_success_without_actual_progress_rejected', 4, lambda m:m.finish_segment(packet, source, now))
    rejects('moving_endpoint_not_success', 4, lambda m:m.finish_segment(changed_packet(body=[*proposal['path'][-1], .04, 0.]), source, now))
    def mutated(m):
        m.path[-1][0]+=.01; m.monitor(packet, source, now)
    rejects('committed_path_mutation_stops', 3, mutated)
    def timeout(m):
        p=copy.deepcopy(packet); p['body_measured_at']=now+36
        s=copy.deepcopy(source); s['decision_at']=now+36
        m.monitor(p, s, now+36)
    rejects('segment_timeout_stops', 3, timeout)
    try:
        m.request(p, source, now)
    except AssertionError:
        checks['identical_causal_information_cannot_loop'] = m.mode=='FAILED'
    else:
        checks['identical_causal_information_cannot_loop'] = False
    checks['frozen_sources_and_inputs_unchanged'] = all(sha(ROOT/p)==value for p,value in frozen.items())
    checks['review_pending_present'] = (ROOT/'REVIEW_PENDING').is_file()
    result = dict(passed=all(checks.values()), checks=checks, models=0, integrations=0,
                  geometric_saved_states=len(cases), synthetic_transaction_events=events,
                  actual_rpp_action_qualified=False, physical_candidate_ready=False,
                  dynamic_acceptance_passed=False,
                  limits=['Saved-state geometry and callback qualification only',
                          'No physical control or measured segment progress',
                          'No new24 acceptance, future information gain or final arrival guarantee'])
    (OUT/'QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
    assert result['passed']


if __name__ == '__main__':
    main()
