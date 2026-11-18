"""Boundary checks independent of ROS/model packages."""
import copy
from contract import command, observation, twist


def run():
    checks = {}
    p = dict(schema=1, run_id='fixture', sequence=1, sampled_at=10.,
             body=[-4., -2., 0., 0., 0.], ranges_m=[3.] * 32)
    c = dict(run_id='fixture', sequence=1, issued_at=10., v=.1, w=.02)
    checks['causal_observation'] = observation(p, run_id='fixture', now=10.01) == p
    checks['representable_command'] = command(c, run_id='fixture', now=10.01) == (.1, .02)

    def reject(name, fn):
        try:
            fn()
        except ValueError:
            checks[name] = True
        else:
            raise AssertionError('NEGATIVE_ACCEPTED ' + name)

    for name, change in [('actor_truth', {'actor_xy': [0, 0]}),
                         ('future_truth', {'future_actor': []}),
                         ('foreign', {'run_id': 'other'}),
                         ('old', {'sampled_at': 9.}),
                         ('future', {'sampled_at': 11.}),
                         ('nan_body', {'body': [0, 0, 0, float('nan'), 0]}),
                         ('wrong_scan', {'ranges_m': [3.] * 31}),
                         ('negative_range', {'ranges_m': [-1.] * 32}),
                         ('too_far_range', {'ranges_m': [3.1] * 32}),
                         ('bool_sequence', {'sequence': True})]:
        bad = dict(copy.deepcopy(p), **change)
        reject(name, lambda bad=bad: observation(bad, run_id='fixture', now=10.01))
    reject('replayed_observation', lambda: observation(p, run_id='fixture', now=10.01, previous_sequence=1))
    for name, change in [('foreign_command', {'run_id': 'other'}),
                         ('old_command', {'issued_at': 9.}),
                         ('future_command', {'issued_at': 11.}),
                         ('nan_command', {'v': float('nan')}),
                         ('speed_command', {'v': .101}),
                         ('curvature_command', {'v': .1, 'w': .1}),
                         ('rotation_command', {'v': 0., 'w': .01})]:
        bad = dict(c, **change)
        reject(name, lambda bad=bad: command(bad, run_id='fixture', now=10.01))
    reject('replayed_command', lambda: command(c, run_id='fixture', now=10.01, previous_sequence=1))
    reject('command_after_stop', lambda: command(c, run_id='fixture', now=10.01, stopped=True))
    checks['reverse_representable'] = twist(-.1, -.02) == (-.1, -.02)
    checks['stop_representable'] = twist(0., 0.) == (0., 0.)
    return dict(passed=all(checks.values()), checks=checks, models=0, physical_native=0)
