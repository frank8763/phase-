"""Exact-or-unknown closing counters, never inferred from process exit codes."""
import copy


def summary(machine):
    value = dict(actual_native=None, own_replay_native=None,
        canonical_vehicle_initializations=None, internal_factory_model_constructions=None,
        independent_Allocator_recomputations=None, private_accounting=None)
    if not isinstance(machine, dict):
        return value
    for key, flag in [('actual_native', 'actual_inflight_unknown'),
                      ('own_replay_native', 'own_replay_inflight_unknown')]:
        count = machine.get(key)
        if machine.get(flag) is False and type(count) is int and 0 <= count <= 40000:
            value[key] = count
    count = machine.get('canonical_vehicle_initializations')
    if type(count) is int and count in (0, 1):
        value['canonical_vehicle_initializations'] = count
    allocation = machine.get('independent_allocation')
    if isinstance(allocation, dict):
        count = allocation.get('allocator_recomputations')
        if allocation.get('allocator_recomputation_inflight_unknown') is False and type(count) is int and 0 <= count <= 40000:
            value['independent_Allocator_recomputations'] = count
    # Keep original native/private machine records as their own evidence.
    # Missing stages/constructions are not supplied as zero by the owner.
    value['private_accounting'] = copy.deepcopy(machine.get('private_current_accounting'))
    return value


def apply_closed(parent, *, round_id, machine, result_path, close_errors):
    value = copy.deepcopy(parent)
    assert value['active_round'] == round_id and value['models_now_authorized'] is True
    assert value.get('active_math_round') is None and value['scientific_revisions'] == 12
    rows = [r for r in value['rounds'] if r['id'] == round_id]
    assert len(rows) == 1
    row = rows[0]
    assert not row.get('owner_accounting_applied', False), 'OWNER_COUNTS_ALREADY_COMMITTED'
    counters = summary(machine)
    for target, source in [('actual_total_native', 'actual_native'),
                           ('own_replay_native', 'own_replay_native')]:
        count = counters[source]
        if count is None:
            row[source + '_unknown'] = True
        else:
            assert type(value[target]) is int and value[target] >= 0
            value[target] += count
            row[source] = count
    # Closing authority is a factual process transition. A scientific result
    # stays pending until the distinct saved native/owner proofs are reviewed.
    row.update(status='CLOSED_OWNER_REVIEW_PENDING', passed=False,
        result=result_path, owner_accounting_applied=True,
        owner_close_error_count=len(close_errors),
        canonical_vehicle_initializations=counters['canonical_vehicle_initializations'],
        internal_factory_model_constructions=None)
    value.update(active_round=None, models_now_authorized=False)
    return value, counters
