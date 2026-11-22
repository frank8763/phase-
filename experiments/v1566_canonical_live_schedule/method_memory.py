"""Durable observer method epoch, separate from measured plant state."""
import copy
import hashlib
import json
import math

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def next_load(prior,v,parked):
    assert type(prior)is bool and type(v)in(int,float)and math.isfinite(v)
    if parked is not None or v<=-.005:return False
    if v>=.005:return True
    return prior

class MethodMemory:
    """Save each applied receipt BEFORE publishing the next method state.

    This is not a sensor, a Predictor, or a plant initializer. Failed saves
    leave published coverage unchanged; an enclosing actual owner must close.
    """
    def __init__(self,method,*,save_receipt):
        clean=copy.deepcopy(method);identity=clean.pop('response_method_sha256')
        assert digest(clean)==identity
        base=method['base_method'];memory=base['method_memory']
        assert memory['steering_load_episode']is False and memory['actual_sensor_claim']is False
        assert memory['epoch_native']==base['fixed_origin_native']
        self.origin=base['fixed_origin_native'];self.method_sha256=identity
        self.covered=self.origin;self.load=False;self.chain='0'*64;self.save_receipt=save_receipt
        self.failed=False
        anchor=dict(kind='DECLARED_OBSERVER_ENTRY_METHOD_EPOCH',epoch_native=self.origin,
            covered_native=self.origin,steering_load_episode=False,actual_sensor_claim=False,
            response_method_sha256=identity,base_method_input_sha256=base['method_input_sha256'],
            previous_chain_sha256=self.chain)
        self.save_receipt(anchor)
        self.anchor_sha256=digest(anchor)

    def applied(self,memory):
        assert not self.failed
        try:
            assert memory['before_native']==self.covered and memory['after_native']==self.covered+1
            assert memory['epoch_native']==self.origin and memory['load_before']is self.load
            assert memory['response_method_sha256']==self.method_sha256 and memory['actual_sensor_claim']is False
            assert memory['previous_chain_sha256']==self.chain
            v,w=memory['applied_body']
            assert all(type(x)in(int,float)and math.isfinite(x)for x in (v,w))
            assert memory['load_after']is next_load(self.load,v,memory['parked_target'])
            for key in ('decision_sha256','source_packet_sha256','source_full_state_sha256','after_full_state_sha256'):
                assert isinstance(memory[key],str)and len(memory[key])==64
            clean=copy.deepcopy(memory);chain=clean.pop('chain_sha256')
            assert digest(clean)==chain
            self.save_receipt(memory)
        except BaseException:
            self.failed=True
            raise
        self.covered=memory['after_native'];self.load=memory['load_after'];self.chain=chain

    def current(self):
        assert not self.failed,'METHOD_MEMORY_SAVE_OR_COVERAGE_FAILED'
        return dict(epoch_native=self.origin,covered_native=self.covered,steering_load_episode=self.load,
            actual_sensor_claim=False,response_method_sha256=self.method_sha256,chain_sha256=self.chain,
            anchor_sha256=self.anchor_sha256,complete_applied_receipt_coverage=True)
