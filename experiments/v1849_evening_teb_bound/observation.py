"""Shared measured receipt used by TEB; original causal clock and 32 rays."""
from context import R,load
shared=load('v1824_exact_shared_clock',R/'experiments/v1694_shared_observation_closure/contract.py')
scan_only=shared.scan_only
def acquire(v,binding,scan):return shared.acquire(v,binding['packet'],scan)
def verify(receipt,expected_native,expected_sim_time):
 p=shared.verify_receipt(receipt,expected_native)
 assert abs(p['sim_time']-expected_sim_time)<=1e-8
 return p
