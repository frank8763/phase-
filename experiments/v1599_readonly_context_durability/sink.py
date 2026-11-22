"""Complete variable witnesses, fixed22MiB stream/32MiB writer, no retries.

Codec is the already qualified lossless original. This adapter changes count
and method binding, not value bytes. It makes no compression-fit claim.
"""
import hashlib
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def load(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def names(proposal):
    n=proposal['nominal_native'];assert 2200<=n<=8200 and n%5==0
    assert proposal['motion_native']==n-2200
    return [f'b{i:04d}_{tag}'for i in range((n-2200)//5+1)for tag in ('current','prospective')]+['nominal']


def binding(method,proposal,*,proposal_sha256,stage,codec):
    assert stage in ('CPP_GENERATION','PYTHON_AUDIT')
    return dict(scientific_integration_revision=12,geometry_kind=method['geometry_kind'],
        response_method_sha256=method['response_method_sha256'],
        base_method_input_sha256=method['base_method_semantic_sha256'],
        causal_snapshot_sha256=method['causal_snapshot_sha256'],segment_sha256=method['segment_sha256'],
        proposal_sha256=proposal_sha256,nominal_native=proposal['nominal_native'],
        stage=stage,ordered_names_sha256=hashlib.sha256(codec.encoded(names(proposal))).hexdigest())


class Sink:
    def __init__(self,*,folder,writer,boundary,method,proposal,proposal_sha256,stage,source):
        self.module=load('v1599_variable_lossless_stream',C/'stream.py',source)
        self.codec=self.module.codec();self.writer=writer;self.folder=Path(folder);self.source=source
        self.stage=stage;self.aborted=False;self.result_attempted=False;self.save_attempted=set();self.raw_attempted=False
        self.stream=self.module.Stream(folder,writer=writer,boundary=boundary,
            binding=binding(method,proposal,proposal_sha256=proposal_sha256,stage=stage,codec=self.codec),ordered_names=names(proposal))

    def data(self,name,arrays,*,accounting,complete):
        assert name not in self.save_attempted;self.save_attempted.add(name)
        self.stream.save_data(name,arrays,accounting=accounting,complete=complete)

    def proof(self,name,value):self.stream.save_proof(name,value)

    def raw_return(self,carrier,*,accounting):
        assert not self.raw_attempted;self.raw_attempted=True
        module=load('v1599_exact_raw_FFI_failure',R/'experiments/v1569_zero_tail_batch_backend/batch_failure.py',self.source)
        proof=module.preserve(carrier,accounting=accounting,
            save_bytes=lambda name,payload:self.codec.write_atomic(self.folder/name,payload,self.writer),
            save_proof=lambda name,value:self.codec.write_atomic(self.folder/name,self.codec.encoded(value),self.writer))
        assert proof is not None and proof['first_error']is None and proof['secondary_errors']==[],repr(proof)

    def abort(self,*,first_error,accounting,branch_name,branch_arrays,nominal_prefix):
        assert not self.aborted;self.aborted=True;secondary=[]
        try:
            if branch_arrays is not None:
                self.stream.emergency(branch_name,branch_arrays,first_error=first_error,
                    accounting=accounting,nominal_prefix=nominal_prefix)
            elif nominal_prefix is not None:
                self.stream.emergency('nominal_partial',nominal_prefix,first_error=first_error,accounting=accounting)
        except BaseException as error:secondary.append('emergency:'+repr(error))
        try:self.stream.abort(first_error=first_error,accounting=accounting)
        except BaseException as error:secondary.append('stream_close:'+repr(error))
        if secondary:raise RuntimeError(repr(secondary))

    def result(self,value):
        assert not self.result_attempted;self.result_attempted=True
        name='GENERATION.json'if self.stage=='CPP_GENERATION'else'AUDIT.json'
        path=self.folder/name
        self.codec.write_atomic(path,self.codec.encoded(value),self.writer)
        if value['passed']:
            assert value['closed']and not self.aborted and value['first_error']is None and value['secondary_errors']==[]
            try:self.stream.seal(generation_result_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            except BaseException as error:
                # Do not overwrite a result already referenced by a possible
                # seal. A separate close failure is required and invalidates
                # the enclosing result/dependency.
                first=repr(error);secondary=None
                try:self.codec.write_atomic(self.folder/'SEAL_FAILURE.json',self.codec.encoded(dict(
                    passed=False,closed=True,first_error=first,result_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())),self.writer)
                except BaseException as saving:secondary=repr(saving)
                raise RuntimeError(dict(first_error=first,secondary=secondary))


def reader(folder,*,method,proposal,proposal_sha256,stage,result_sha256,source,check):
    folder=Path(folder);assert not (folder/'SEAL_FAILURE.json').exists()and not(folder/'STREAM_ABORT.json').exists()
    module=load('v1599_verified_variable_reader',C/'stream.py',source);codec=module.codec()
    return module.Reader(folder,expected_binding=binding(method,proposal,proposal_sha256=proposal_sha256,stage=stage,codec=codec),
        expected_result_sha256=result_sha256,ordered_names=names(proposal),check=check)
