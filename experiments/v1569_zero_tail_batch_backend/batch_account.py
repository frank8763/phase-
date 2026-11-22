"""Native claims; no model, numerical library, FFI or authority creation."""
NATIVE_CAP=1263600
WITNESS_CAP=1250000
NOMINAL_CAP=13600


class WorkLedger:
    def __init__(self):
        self.value=dict(native=0,nominal_native=0,witness_native=0,bucket=None,
            inflight_unknown=False,inflight_bucket=None,inflight_claimed_native=0,
            Predictor=0,Engine=0,copy=0,construction_inflight=None,
            batch_calls=0,batch_native=0)

    def bucket(self,name):
        v=self.value
        assert name in {'nominal','witness'}and not v['inflight_unknown']and v['construction_inflight']is None
        v['bucket']=name

    def claim(self,count,*,batch=False):
        v=self.value
        assert type(count)is int and count==(2199 if batch else 1),'CPP_BATCH_EXACT_NATIVE_CLAIM'
        assert not v['inflight_unknown']and v['construction_inflight']is None
        bucket=v['bucket'];assert bucket in {'nominal','witness'}
        assert not batch or bucket=='witness','CPP_BATCH_ONLY_WITNESS_ZERO_TAIL'
        assert v['native']+count<=NATIVE_CAP,'CPP_FULL_NATIVE_BUDGET'
        assert v[bucket+'_native']+count<=(NOMINAL_CAP if bucket=='nominal'else WITNESS_CAP),'CPP_CATEGORY_NATIVE_BUDGET'
        v.update(inflight_unknown=True,inflight_bucket=bucket,inflight_claimed_native=count)

    def acknowledge(self,count,*,batch=False):
        v=self.value
        assert type(count)is int and count==(2199 if batch else 1)
        assert v['inflight_unknown']and v['inflight_claimed_native']==count
        v['native']+=count;v[v['inflight_bucket']+'_native']+=count
        if batch:v['batch_native']+=count;v['batch_calls']+=1
        v.update(inflight_unknown=False,inflight_bucket=None,inflight_claimed_native=0)

    def construct(self,kind):
        v=self.value;assert kind in {'Engine','copy'}
        assert not v['inflight_unknown']and v['construction_inflight']is None
        assert v[kind]<(1 if kind=='Engine'else 562)
        v['construction_inflight']=kind

    def constructed(self,kind):
        v=self.value;assert v['construction_inflight']==kind
        v[kind]+=1;v['construction_inflight']=None

    def counts(self):return self.value.copy()
