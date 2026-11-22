"""Exact dynamic work ledger. Claims precede calls; exceptions stay unknown.

No models, libraries, filesystem writes or admission creation here. Proposal,
complete CPP generation and independent Python audit have separate ledgers.
"""
import copy


class Work:
    def __init__(self, *, native, nominal, witness, copies, engine, predictor, batch_calls):
        self.caps=dict(native=native,nominal_native=nominal,witness_native=witness,
            copy=copies,Engine=engine,Predictor=predictor,batch_calls=batch_calls)
        assert all(type(v)is int and v>=0 for v in self.caps.values())
        assert native==nominal+witness
        self.value=dict(native=0,nominal_native=0,witness_native=0,copy=0,Engine=0,Predictor=0,
            batch_calls=0,batch_native=0,bucket=None,inflight_unknown=False,
            inflight_claimed_native=0,inflight_bucket=None,construction_inflight=None)

    def bucket(self,name):
        self.idle();assert name in ('nominal','witness');self.value['bucket']=name

    def idle(self):
        assert not self.value['inflight_unknown']and self.value['construction_inflight']is None

    def claim(self,count,*,batch=False):
        self.idle();v=self.value
        assert type(count)is int and count==(2199 if batch else 1)
        category=v['bucket'];assert category in ('nominal','witness')
        assert not batch or category=='witness'
        assert v['native']+count<=self.caps['native'],'GOAL_BOUND_TOTAL_NATIVE_CAP'
        assert v[category+'_native']+count<=self.caps[category+'_native'],'GOAL_BOUND_CATEGORY_NATIVE_CAP'
        assert not batch or v['batch_calls']<self.caps['batch_calls']
        v.update(inflight_unknown=True,inflight_claimed_native=count,inflight_bucket=category)

    def acknowledge(self,count,*,batch=False):
        v=self.value;assert type(count)is int and count==(2199 if batch else 1)
        assert v['inflight_unknown']and v['inflight_claimed_native']==count
        v['native']+=count;v[v['inflight_bucket']+'_native']+=count
        if batch:v['batch_native']+=count;v['batch_calls']+=1
        v.update(inflight_unknown=False,inflight_claimed_native=0,inflight_bucket=None)

    def construct(self,kind):
        self.idle();assert kind in ('copy','Engine','Predictor')
        assert self.value[kind]<self.caps[kind],'GOAL_BOUND_CONSTRUCTION_CAP'
        self.value['construction_inflight']=kind

    def constructed(self,kind):
        assert self.value['construction_inflight']==kind
        self.value[kind]+=1;self.value['construction_inflight']=None

    def counts(self):return copy.deepcopy(self.value)

    def complete(self):
        self.idle()
        assert all(self.value[k]==v for k,v in self.caps.items()),'INCOMPLETE_GOAL_BOUND_WORK'
