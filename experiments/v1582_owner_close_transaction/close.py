"""Explicit first-error-preserving owner cleanup; no runtime/model authority.

Callbacks are supplied by the future source-bound production owner. This helper
does not synthesize counts, navigation acceptance or OS process identities.
"""
import copy
import traceback


def close_owner(*, children, close_child, child_closed, drain, close_logs,
                read_machine, restore_review, verify_review, verify_lock_idle,
                save_receipt, close_parent, first_error=None, prior_errors=()):
    result = dict(closed=False, close_complete=False, runtime_pass_not_inferred=True,
        first_error=copy.deepcopy(first_error), errors=copy.deepcopy(list(prior_errors)),
        child_exit_verified={}, all_children_closed=False, lock_idle=False,
        review_original_restored=False, parent_closed=False,
        machine=None, machine_counts_unknown=True, close_receipt_saved=False)

    def attempt(stage, action):
        try:
            return True, action()
        except BaseException as error:
            item = dict(stage=stage, error=repr(error), traceback=traceback.format_exc())
            if result['first_error'] is None:
                result['first_error'] = copy.deepcopy(item)
            result['errors'].append(item)
            return False, None

    # A failure to close one child never skips the other owned children.
    for label, child in children.items():
        attempt('CLOSE_OWNED_' + label, lambda child=child: close_child(child))
    attempt('DRAIN_OUTPUTS', drain)
    attempt('CLOSE_LOGS', close_logs)
    for label, child in children.items():
        ok, exited = attempt('VERIFY_EXIT_' + label, lambda child=child: child_closed(child))
        result['child_exit_verified'][label] = bool(ok and exited is True)
    result['all_children_closed'] = all(result['child_exit_verified'].values())
    if result['all_children_closed']:
        ok, idle = attempt('VERIFY_NATIVE_LOCK_IDLE', verify_lock_idle)
        result['lock_idle'] = bool(ok and idle is True)

    # Do not publish a stopped system or restore a review hold while an owned
    # native owner might still be executing. Unknown stays active for recovery.
    safe_to_close = result['all_children_closed'] and result['lock_idle']
    if safe_to_close:
        attempt('RESTORE_ORIGINAL_REVIEW', restore_review)
        ok, original = attempt('VERIFY_ORIGINAL_REVIEW', verify_review)
        result['review_original_restored'] = bool(ok and original is True)
    ok, machine = attempt('READ_NATIVE_MACHINE', read_machine)
    if ok and isinstance(machine, dict):
        result['machine'] = machine
        result['machine_counts_unknown'] = bool(machine.get('actual_inflight_unknown', True)
            or type(machine.get('actual_native')) is not int)

    # Preserve a prepared close record even when review/worker verification
    # refused. Parent callback receives the real machine or explicit unknown;
    # this helper never fills missing model/initialization/native counters.
    ok, _ = attempt('SAVE_PREPARED_CLOSE', lambda: save_receipt('PREPARED', copy.deepcopy(result)))
    result['close_receipt_saved'] = ok
    if safe_to_close and result['review_original_restored']:
        ok, acknowledged = attempt('CLOSE_PARENT_AUTHORITY',
            lambda: close_parent(copy.deepcopy(result)))
        result['parent_closed'] = bool(ok and acknowledged is True)
    result['closed'] = safe_to_close
    result['close_complete'] = bool(safe_to_close and result['review_original_restored']
        and result['parent_closed'] and result['close_receipt_saved'])
    ok, _ = attempt('SAVE_FINAL_CLOSE', lambda: save_receipt('FINAL', copy.deepcopy(result)))
    if not ok:
        result['close_receipt_saved'] = False
        result['close_complete'] = False
    return result
