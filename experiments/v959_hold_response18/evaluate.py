"""Explicitly approved steering-hold response contract, full handoff stays separate."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v959_response_contract',ROOT/'experiments/v958_hold_steering_contract/response_contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)


def evaluate(data,servo,origin,task,handoff=False):
    if handoff:return contract.base.evaluate(data,servo,origin,task,handoff=True)
    return contract.evaluate(data,servo,origin,task)
