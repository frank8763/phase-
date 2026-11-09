"""Bind production router/command records to reference-loss recovery entry."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'experiments/v936_rpccr_corridor_search'),
               str(ROOT/'experiments/v938_rpccr_recovery_segments')]
from reference_loss import ReferenceLoss
from transaction import RecoveryTransaction


class ReferenceWatchdog:
    def __init__(self, original_goal, known, route_index=0, command_index=0):
        self.detector = ReferenceLoss()
        self.transaction = RecoveryTransaction(original_goal, known)
        self.route_index = route_index
        self.command_index = command_index

    def poll(self, routes, decisions, packet, source, now):
        while self.route_index < len(routes):
            route = routes[self.route_index]
            completed = route['started_monotonic']+route['wall_s']
            if completed > now:
                break
            self.detector.route(completed, route['passed'])
            self.route_index += 1
        while self.command_index < len(decisions):
            row = decisions[self.command_index]
            if row['proof']['issued_at'] > now:
                break
            self.detector.command(row['proof']['issued_at'], *row['wanted'])
            self.command_index += 1
        if self.transaction.mode != 'NORMAL':
            return None
        event = self.detector.observe(packet, source, now)
        if not event['triggered']:
            return None
        cancel = self.transaction.request(packet, source, now)
        return dict(trigger=event, effect=cancel)
