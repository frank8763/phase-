"""Replay actual immutable history through the exact production watchdog binding."""
import ast
import gzip
import hashlib
import importlib.abc
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).parent
OUT = ROOT/'runs/v941_rpccr_reference_loss_binding'
SAVED = ROOT/'runs/v936_rpccr_corridor_search'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'factory', 'physical', 'vehicle', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(CODE))
from watchdog import ReferenceWatchdog


def main():
    OUT.mkdir(exist_ok=False)
    known = json.loads((SAVED/'saved/SETUP.json').read_text())['known']
    rows = json.loads(gzip.decompress((SAVED/'saved/COMMAND_TUBES.json.gz').read_bytes()))
    routes = json.loads((SAVED/'saved/ROUTER_REQUESTS.json').read_text())
    watchdog = ReferenceWatchdog([4., -2.], known)
    trigger, index = None, None
    for index, row in enumerate(rows):
        trigger = watchdog.poll(routes, rows, row['packet'], row['source'], row['proof']['issued_at'])
        if trigger is not None:
            break
    expected = json.loads((SAVED/'ENTRY_QUALIFICATION.json').read_text())['first_actual_trigger']
    checks = dict(actual_history_triggers_at_original_first_trigger=trigger is not None and trigger['trigger']['body_native_tick']==expected['body_native_tick'],
                  automatic_effect_is_cancel_before_any_follow=trigger is not None and trigger['effect']['action']=='CANCEL_NORMAL_NAVIGATION',
                  no_twist_is_dispatched_by_binding=not any(e['action'].startswith('SEND_') for e in watchdog.transaction.events),
                  exactly_one_recovery_entry=watchdog.transaction.mode=='CANCEL_PENDING')
    row = rows[index]
    checks['duplicate_poll_does_not_duplicate_cancel'] = watchdog.poll(routes, rows, row['packet'], row['source'], row['proof']['issued_at']) is None
    for source in CODE.glob('*.py'):
        ast.parse(source.read_text(), filename=str(source))
    checks['installed_rpp_handoff_qualified'] = json.loads((ROOT/'runs/v940_rpccr_handoff_entry/RESULT.json').read_text())['passed']
    checks['independent_four_corridor_and_transaction_qualified'] = json.loads((ROOT/'runs/v938_rpccr_recovery_segments/QUALIFICATION.json').read_text())['passed']
    checks['review_pending_intact'] = hashlib.sha256((ROOT/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    result = dict(passed=all(checks.values()), checks=checks, models=0, integrations=0,
                  original_tick=expected['body_native_tick'], actual_history_rows_until_trigger=index+1,
                  effect=trigger, physical_authorized=False, dynamic_acceptance_passed=False,
                  limits='Production trigger binding and installed RPP software qualified separately; complete supervisor closed-loop/native evidence still unexecuted.')
    files = sorted(CODE.glob('*'))
    (OUT/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}, models=0, integrations=0), indent=2)+'\n')
    (OUT/'QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    assert result['passed']


if __name__=='__main__':
    main()
