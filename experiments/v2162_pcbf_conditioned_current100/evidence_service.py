"""Charged durable full-array/recipe records, one original shared work cap."""
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace
from context import R,C,load,digest


class Arrays:
    def __init__(self,values):self.values=values
    def __enter__(self):return self.values
    def __exit__(self,*args):return False


class Service:
    MAX_REBUILD_NATIVE=500000
    def __init__(self,q,*,setup,task,source,out,quota,ledger,window):
        self.q=q;self.np=q.np;self.setup=setup;self.out=Path(out);self.ledger=ledger
        self.window=window;self.quota=quota;self.poisoned=False;self.attempted=set()
        self.recipe=load('recipe',R/'experiments/v1907_dwa_reconstruction_contract/recipe.py')
        self.cache_class=load('v1912_exact_audit_cache',R/'experiments/v1907_dwa_reconstruction_contract/audit_cache.py').AuditCache
        self.cache=self.cache_class()
        self.escrow=load('v1912_exact_work_escrow',R/'experiments/v1907_dwa_reconstruction_contract/escrow.py').WorkEscrow(ledger.limits['python_native_cap'])
        self.codec=load('v1912_exact_array_codec',R/'experiments/v1902_dwa_lossless_evidence/array_bits.py')
        self.pack=load('v1912_exact_proof_pack',R/'experiments/v1903_dwa_durable_proof_pack/proof_pack.py')
        self.writer=self.pack.AppendWriter(self.out/'DWA_PREDICTIONS.pack',quota,lambda p,m:p.open(m))
        self.reconstruct,proof=load('v1912_exact_rebuild_loop',R/'experiments/v1911_dwa_resource_bootstrap_reconstruction/rebuild.py').bind((C/'response.py').read_text(),dict(sys=__import__('sys')))
        assert proof['original_model_loop_AST_exact']
        self.binding=dict(source_files_sha256=digest(source),task_sha256=digest(task),setup_sha256=digest(setup),response_source_sha256=source['experiments/v1863_remaining_routes_dwa/response.py'])
        self.live_canary_passed=False;self.recipe_native=0;self.rebuilt_native=0;self.rebuild_s=0.;self.full_records=0;self.recipe_records=0
        original=ledger.before
        def before(kind,count):
            if kind=='python':
                if self.escrow.active is None:self.escrow.before_online(ledger.python,count)
                else:self.escrow.before_rebuild(ledger.python,count)
            return original(kind,count)
        ledger.before=before

    def persist(self,proof,arrays):
        assert not self.poisoned and proof['arrays']not in self.attempted,'PREDICTION_RECORD_NO_RETRY'
        self.attempted.add(proof['arrays']);self.poisoned=True
        if not self.live_canary_passed:
            # One counted fresh prediction canary, no second plant/factory.
            rebuilt=self.reconstruct(self.q,self.setup,proof['origin_packet'],arrays['requests'],None,None)
            assert {k:self.recipe.array_identity(v)for k,v in rebuilt.items()}=={k:self.recipe.array_identity(v)for k,v in arrays.items()},'FRESH_RECIPE_CANARY_BITS'
            self.live_canary_passed=True
        n=proof['native'];key=proof['arrays']
        record=self.recipe.build(proof,arrays,self.binding)
        identity=record['arrays']
        # Fixed storage rule, independent of numerical outcomes. Non-goal
        # predictions rebuild exact bits under escrow from the ORIGINAL cap.
        mode='FULL_ARRAYS'if key.endswith('_goal_stop.npz')else'RECIPE'
        recipe_raw=json.dumps(record,separators=(',',':'),allow_nan=False).encode()
        if mode=='FULL_ARRAYS':
            class Mapping:
                files=list(arrays)
                def __getitem__(self,key):return arrays[key]
            raw=self.pack.array_container(self.np,Mapping(),self.codec.encode)
        else:
            assert self.recipe_native+n<=self.MAX_REBUILD_NATIVE,'EXACT_REBUILD_NATIVE_CAP'
        if mode=='RECIPE':
            self.escrow.reserve(key,n,self.ledger.python)
            receipt=self.writer.append(key,recipe_raw);self.recipe_native+=n;self.recipe_records+=1
        else:
            receipt=self.writer.append(key,raw);self.full_records+=1
        receipt.update(mode=mode,arrays_identity=identity,proof_digest=self.recipe.digest(proof),binding=self.binding)
        self.poisoned=False
        return receipt

    def clean_proof(self,proof):return {k:v for k,v in proof.items()if k!='hybrid_evidence'}
    def load_full(self,proof):
        assert not self.poisoned,'PREDICTION_SERVICE_POISONED'
        key=proof['arrays'];receipt=proof['hybrid_evidence'];clean=self.clean_proof(proof)
        assert receipt['committed'] and receipt['name']==key and receipt['binding']==self.binding
        assert receipt['proof_digest']==self.recipe.digest(clean),'PREDICTION_PROOF_DIGEST'
        self.poisoned=True
        try:
            with (self.out/'DWA_PREDICTIONS.pack').open('rb')as stream:raw,end=self.pack.read_record(stream,receipt['offset'],key)
            assert end==receipt['offset']+receipt['frame_bytes']
            if receipt['mode']=='FULL_ARRAYS':arrays=self.pack.read_arrays(raw,self.codec.decode)
            else:
                assert receipt['mode']=='RECIPE'
                record=json.loads(raw);self.escrow.begin(key,self.ledger.python);start=time.monotonic()
                try:
                    arrays=self.recipe.regenerate(record,clean,self.binding,lambda packet,requests:self.reconstruct(self.q,self.setup,packet,requests,None,None))
                    self.escrow.finish(self.ledger.python)
                except BaseException:self.escrow.fail();raise
                self.rebuilt_native+=proof['native'];self.rebuild_s+=time.monotonic()-start
            assert {k:self.recipe.array_identity(a)for k,a in arrays.items()}==receipt['arrays_identity'],'PREDICTION_ARRAY_IDENTITY'
            self.cache.remember_full_verified(key,arrays,is_goal=key.endswith('_goal_stop.npz'))
            self.poisoned=False
            return Arrays(arrays)
        except BaseException:raise

    def confirm_full_geometry(self,proof):self.cache.confirm_full_geometry(proof['arrays'])
    def load_prefix_after_full(self,proof):return Arrays(self.cache.prefix_after_full(proof['arrays'],proof['hybrid_evidence']['arrays_identity']))
    def load_goal_after_full(self,proof):return Arrays(self.cache.whole_goal_after_full(proof['arrays'],proof['hybrid_evidence']['arrays_identity']))
    def snapshot(self):
        return dict(full_records=self.full_records,recipe_records=self.recipe_records,recipe_reserved_native=self.recipe_native,
                    rebuilt_native=self.rebuilt_native,rebuild_wall_s=self.rebuild_s,unspent_audit_holds=dict(self.escrow.holds),
                    poisoned=self.poisoned or self.escrow.poisoned,original_python_subset_cap=self.escrow.cap,
                    maximum_rebuild_subset_native=self.MAX_REBUILD_NATIVE,total_modelwork=None,live_reconstruction_canary_passed=self.live_canary_passed,
                    cache_bytes=self.cache.bytes(),pack_bytes=self.writer.offset)
