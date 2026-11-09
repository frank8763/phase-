"""Real supervisor transitions with controlled action futures, zero ROS/models."""
import importlib.abc, json, pathlib, sys, types
from unittest.mock import patch

R = pathlib.Path(__file__).resolve().parents[2]
C = R / 'experiments/v903_retained_exit_reference'
O = R / 'runs/v903_retained_exit_reference'
sys.path.insert(0, str(C))

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'mujoco', 'torch', 'rclpy', 'physical', 'vehicle'}:
            raise AssertionError('FORBIDDEN_IMPORT ' + fullname)

sys.meta_path.insert(0, NoModel())
import supervise as production

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def case(kind):
    clock = [100.]
    issued = []
    canceled = []
    class Future:
        def __init__(self, value, at=0.):
            self.value, self.at = value, at
        def done(self):
            return clock[0] >= self.at
        def result(self):
            require(self.done(), 'FUTURE_NOT_DONE')
            return self.value
    class Handle:
        accepted = True
        def __init__(self, role, index):
            self.role = role
            status = 6 if kind == 'refuge_failed' and role == 'REFUGE' else 4
            at = clock[0] + (.3 if role == 'REFUGE' and kind not in ['region_resume','cancel_rejected','never_stops','no_new_hit'] else 100.)
            if index > 1 or kind == 'plain_success':
                at = clock[0] + .3
            self.future = Future(types.SimpleNamespace(status=status, result=types.SimpleNamespace(error_code=0)), at)
        def get_result_async(self):
            return self.future
        def cancel_goal_async(self):
            canceled.append(self.role)
            self.future.at = clock[0]
            self.future.value.status = 5
            return Future(types.SimpleNamespace(goals_canceling=[] if kind=='cancel_rejected' and self.role=='REFUGE' else [1]))
    proxy = types.SimpleNamespace(refuge_mode=False, refuge_selection=None, known={})
    class Action:
        def send_goal_async(self, goal):
            role = 'REFUGE' if proxy.refuge_mode else 'ORIGINAL'
            issued.append(role)
            return Future(Handle(role, len(issued)-1))
    class Lock:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    tracker = types.SimpleNamespace(support=__import__('numpy').zeros(16), latest={'native_tick': 1}, when=100., last_hit=102.)
    motion = types.SimpleNamespace(lock=Lock(), tracker=tracker, scan_monotonic=100.)
    node = types.SimpleNamespace(latest={'sent_at': 100., 'native_tick': 1, 'body': [0.,0.,0.,0.,0.]}, motion=motion,
                                 action=Action(), planner_proxy=proxy, breadcrumbs=[], supervision_events=[])
    node.get_clock = lambda: types.SimpleNamespace(now=lambda: types.SimpleNamespace(to_msg=lambda: None))
    goal = types.SimpleNamespace(pose=types.SimpleNamespace(header=types.SimpleNamespace(stamp=None), pose=types.SimpleNamespace(position=types.SimpleNamespace(x=4., y=0.), orientation=types.SimpleNamespace(z=0., w=1.))))
    def spin(*args, **kwargs):
        clock[0] += .05
        node.latest['native_tick'] += 5
        node.latest['body'][3] = .1 if kind=='never_stops' and len(issued)>1 else 0.
        node.latest['sent_at'] = clock[0] - (1. if kind == 'stale' else 0.)
        motion.scan_monotonic = clock[0]
        tracker.when = clock[0]
        tracker.last_hit = 0. if kind=='no_new_hit' else clock[0] + .1
    def wait(n, predicate, until, message):
        for _ in range(100):
            if predicate():
                return
            spin()
            require(clock[0] < until, message)
        raise AssertionError('UNBOUNDED_FAKE_WAIT')
    def hold(*args, **kwargs):
        return kind == 'plain_success' or kwargs.get('hold') != 6. or len(issued) > 1
    selection = None if kind == 'no_refuge' else {'goal': [-1.,0.,0.], 'breadcrumb_native_tick': 0}
    error = None
    with patch.object(production.time, 'monotonic', lambda: clock[0]), patch.object(production.time, 'time', lambda: 1000.), patch.object(production, 'wait_ok', hold), patch.object(production, 'choose_refuge', lambda *args: selection), patch.object(production,'membership',lambda *args: {'passed':kind in ['region_resume','cancel_rejected','never_stops','no_new_hit']}):
        try:
            response, events = production.supervise(node, goal, 130., 2000., spin, wait, require, lambda: None)
            status = response.status
        except RuntimeError as e:
            error, status, events = str(e), None, node.supervision_events
    if kind == 'plain_success':
        passed = status == 4 and issued == ['ORIGINAL'] and not canceled
    elif kind == 'point_resume':
        passed = status == 4 and issued == ['ORIGINAL','REFUGE','ORIGINAL'] and canceled == ['ORIGINAL'] and [x['event'] for x in events] == ['REFUGE_REQUEST','REFUGE_ACTION_REACHED','REFUGE_STOP_CONFIRMED','ORIGINAL_GOAL_RESUMED']
    elif kind == 'no_refuge':
        passed = error == 'NO_CAUSAL_ADMITTED_REFUGE' and issued == ['ORIGINAL'] and not canceled
    elif kind == 'stale':
        passed = error == 'STALE_REFUGE_ODOMETRY' and issued == ['ORIGINAL']
    elif kind=='region_resume':
        passed = status==4 and issued==['ORIGINAL','REFUGE','ORIGINAL'] and canceled==['ORIGINAL','REFUGE'] and [x['event'] for x in events]==['REFUGE_REQUEST','REFUGE_SET_ENTERED','REFUGE_STOP_CONFIRMED','ORIGINAL_GOAL_RESUMED']
    elif kind in ['cancel_rejected','never_stops','no_new_hit']:
        expected={'cancel_rejected':'REFUGE_SET_CANCEL_REJECTED','never_stops':'REFUGE_SET_BRAKING_TWO_SECONDS_LIMIT','no_new_hit':'NAVIGATION_DEADLINE'}
        passed=error==expected[kind] and issued==['ORIGINAL','REFUGE']
    else:
        passed = error == 'REFUGE_ACTION_FUNCTIONAL_FAILURE' and issued == ['ORIGINAL','REFUGE']
    return dict(case=kind, passed=passed, action_roles=issued, cancels=canceled, error=error)

def main():
    rows = [case(x) for x in ['plain_success','point_resume','region_resume','cancel_rejected','never_stops','no_new_hit','no_refuge','stale','refuge_failed']]
    # Load the same lazy imports, in production order. Dependencies may mutate sys.path.
    sys.path.insert(0,str(C))
    import motion_publisher
    sys.path.insert(0,str(C))
    import dynamic_proxy
    identity = pathlib.Path(motion_publisher.__file__).parent == C and pathlib.Path(dynamic_proxy.__file__).parent == C
    result = dict(passed=all(x['passed'] for x in rows) and identity, cases=rows, production_module_identity=identity,
                  models=0, integrations=0, scope='Real supervisor state machine with fake action futures; not physical navigation')
    (O/'SUPERVISION_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
