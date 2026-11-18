"""Zero-prediction check of explicit new-window context at the full call site."""
import ast
import inspect
import json
import time
from qualify_entry import C,R,O,q
import live_entry


def main():
    assert not (O/'LIVE_BINDING.json').exists()
    path=C/'live_entry.py'
    tree=ast.parse(path.read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='execute')
    calls=[n.func.id for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)]
    assert 'remaining' not in calls and calls.count('remaining_fn')>=3
    assert 'remaining_fn' in inspect.signature(live_entry.execute).parameters
    assert live_entry.goal_entry.execute.__module__=='goal_entry'
    rejected=[]
    for name,end,budget in [('closed',time.time()-1,1000.),('insufficient',time.time()+1000,1.)]:
        try:
            live_entry.execute(None,None,None,end,None,None,None,None,remaining_fn=lambda:budget)
        except AssertionError as exc:
            assert str(exc)=='NEW_WINDOW_RESERVE_REQUIRED'
            rejected.append(name)
        else:raise AssertionError('CLOSED_WINDOW_ACCEPTED')
    try:live_entry.execute(None,None,None,time.time()+1000,None,None,None,None)
    except TypeError:rejected.append('missing_new_context')
    else:raise AssertionError('OLD_WINDOW_CONTEXT_IMPLICITLY_REUSED')
    freeze={str(p.relative_to(R)):q.sha(p)for p in [path,C/'check_live_binding.py',C/'SOURCE_FREEZE.json']}
    q.dump(C/'LIVE_ENTRY_BINDING_FREEZE.json',dict(files=freeze,
        scope='zero-model context binding extension; original frozen draft retained'))
    q.dump(O/'LIVE_BINDING.json',dict(passed=True,rejected=rejected,
        explicit_new_window_required=True,no_old_window_calls=True,models=0,
        analytical_cpp_native=0,analytical_python_native=0,
        full_physical_worker_qualified=False))
    print('new-window binding: 3 rejects PASS; no model or prediction')


if __name__=='__main__':main()
