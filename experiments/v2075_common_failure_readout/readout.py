"""Hash-bound reporting, not another numerical or physical audit."""
from pathlib import Path
import collections, copy, datetime, hashlib, json, os

R = Path(__file__).resolve().parents[2]
O = R / 'runs/v2075_common_failure_readout'

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    os.sched_setaffinity(0, {5})
    os.nice(max(0, 19-os.getpriority(os.PRIO_PROCESS, 0)))
    O.mkdir(exist_ok=True)
    assert not (O/'RESULT.json').exists()
    base = R/'runs/v1805_common_algorithm_registry'
    pins = {}
    def bound(path, expected=None):
        h = sha(path)
        if expected is not None:
            assert h == expected, 'BOUND_RESULT_CHANGED:'+str(path)
        pins[str(path.relative_to(R))] = h
        return read(path)
    ledger = bound(base/'LEDGER.json')
    slots = copy.deepcopy(ledger['slots'])
    for p in sorted((base/'PARALLEL_METHOD_EVENTS').glob('*.REGISTERED.json')):
        event = bound(p)
        slot = next(x for x in slots if (x['method'],x['task_id']) == (event['method'],event['task_id']))
        assert not slot['registered']
        slot.update(event)
        closed = p.with_name(p.name.replace('.REGISTERED.json','.CLOSED.json'))
        if closed.exists():
            final = bound(closed)
            assert final['registration_sha256'] == sha(p)
            slot.update(final)
    assert len(slots) == 120
    rows = []
    for slot in slots:
        row = {k:slot[k] for k in ['method','task_id','case_id','registered','closed']}
        if not slot['registered']:
            kind = 'UNEXECUTED'
        elif not slot['closed']:
            kind = 'ACTIVE'
        elif slot.get('qualified_success'):
            kind = 'WHOLE_ARRIVAL'
        elif slot.get('valid_finite_method_refusal') or slot.get('status') == 'VALID_FINITE_METHOD_REFUSAL_WITH_INDEPENDENT_PREFIX_AUDIT':
            kind = 'VALID_FINITE_REFUSAL'
        else:
            kind = 'TECHNICAL_OR_UNQUALIFIED_CENSOR'
        row['outcome'] = kind
        if slot['closed']:
            result_path = R/slot['result_path']
            result = bound(result_path, slot['result_sha256'])
            error = result.get('machine_first_error') or result.get('first_error')
            if error is None:
                error = (slot.get('first_error') or slot.get('technical_failure'))
            message = error.get('error',str(error)) if isinstance(error,dict) else error
            audit = result.get('independent_audit') or {}
            row.update(first_error=message,
                       actual_native=result.get('actual_native'),
                       replay_native=result.get('own_replay_native'),
                       prefix_audit_passed=audit.get('passed'),
                       result_path=slot['result_path'])
        rows.append(row)
    methods = {}
    for name in dict.fromkeys(x['method'] for x in rows):
        group = [x for x in rows if x['method']==name]
        methods[name] = dict(outcomes=dict(collections.Counter(x['outcome'] for x in group)),
                             first_errors=dict(collections.Counter(x.get('first_error') or 'NONE' for x in group if x['closed'])))
    value = dict(closed=True, reporting_passed=True,
                 checked_local=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
                 denominator=120, methods=methods, slots=rows, input_hashes=pins,
                 models=0, physics=0, replay=0, optimizer_calls=0,
                 new_independent_safety_audit=False, mechanism_attribution=False,
                 all_failures_retained=True, old_ledger_unchanged=True)
    assert all(sha(R/n)==h for n,h in pins.items()), 'INPUT_CHANGED_DURING_READOUT'
    raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    assert len(raw.encode())<256*1024
    (O/'RESULT.json').write_text(raw)
    print(json.dumps(dict(checked_local=value['checked_local'],methods=methods),ensure_ascii=False))

if __name__ == '__main__':
    main()
