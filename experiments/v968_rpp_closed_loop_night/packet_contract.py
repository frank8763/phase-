"""Declared V961 dependency, source-frozen before models."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v963_packet_contract',ROOT/'experiments/v961_steering_continuity/packet_contract.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
policy_packet=module.policy_packet
