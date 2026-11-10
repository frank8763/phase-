"""Exact frozen recovery transaction, with explicit revised guard binding only."""
import importlib.util
import sys
from pathlib import Path

C = Path(__file__).parent
R = C.resolve().parents[1]
sys.path[:0] = [str(C), str(R/'experiments/v977_state_consistent_recovery')]
from tracking import TrackingGuard, fingerprint

spec = importlib.util.spec_from_file_location('v981_frozen_transaction', R/'experiments/v977_state_consistent_recovery/transaction.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.TrackingGuard = TrackingGuard
RecoveryTransaction = base.RecoveryTransaction
