"""Direction lifecycle only. Creates no actuator permission or safety certificate."""
import copy
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'experiments/v947_rpccr_forward_commitment'))
from direction_contract import require_forward_path, require_forward_request


class ForwardNavigation:
    def __init__(self, goal):
        if len(goal) != 2 or not all(math.isfinite(x) for x in goal):
            raise ValueError('INVALID_ORIGINAL_GOAL')
        self.original_goal = tuple(goal)
        self.replan_requested = False
        self.replan_count = 0
        self.events = []

    def request(self, v, w):
        if not math.isfinite(v) or not math.isfinite(w):
            raise ValueError('NONFINITE_CONTROL')
        if v < 0:
            self.replan_requested = True
            self.events.append(dict(action='CANCEL_AND_REPLAN_FORWARD', wanted=[v,w]))
            return False
        require_forward_request(v, w)
        return True

    def reference(self, path):
        return require_forward_path(path)

    def resume(self, goal):
        if tuple(goal) != self.original_goal:
            raise ValueError('ORIGINAL_GOAL_CHANGED')
        self.replan_requested = False
        self.replan_count += 1
        event = dict(action='NAVIGATE_FORWARD_TO_ORIGINAL_GOAL',
                     goal=list(self.original_goal), original_goal_success=False)
        self.events.append(event)
        return copy.deepcopy(event)

    def reverse_escape(self, *args):
        raise ValueError('REVERSE_ESCAPE_NOT_QUALIFIED')
