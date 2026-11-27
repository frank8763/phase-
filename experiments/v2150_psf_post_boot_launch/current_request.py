"""Fresh measured current at each native5 cycle; no fullstate or actor truth to peer."""
from context import R,C,SOURCE,O,METHOD,read,load,digest,sha

def build(np,receipt,fullstate,selected,source,*,run_id,causal=None):
 known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
 for path in[C/'request.py',C/'filter.py',C/'geometry.py',C/'kinematics.py',C/'nominal.py',R/'experiments/v855_renewal_worker/KNOWN_FIELD.json']:
  assert source[str(path.relative_to(R))]==sha(path),'FILTER_SOURCE_IDENTITY_CHANGED'
 k=receipt['packet']['native_tick'];assert type(k)is int and k%5==0 and 0<=k<57800,'FILTER_CURRENT_COMPONENT_CLOCK'
 p=load('filter_original_observation',C/'observation.py').verify(receipt,k,.01*k)
 nominal=load('filter_shared_nominal',C/'nominal.py').command(p,selected)
 deps=load('filter_source_scoped_dependencies',C/'filter_scope.py')
 with deps.scope(source)as modules:clean=modules.request.build(receipt,known,nominal['request'][:2],selected['gear'],causal)
 clean.update(schema='FRESH_RECEDING_FILTER_PROPOSAL_INPUT_V1',run_id=run_id,method=METHOD,nominal_source=nominal,source_manifest_sha256=digest({str(x.relative_to(R)):sha(x)for x in[C/'filter.py',C/'geometry.py',C/'kinematics.py',C/'nominal.py']}))
 clean['input_sha256']=digest(clean)
 request=dict(schema='FILTER_CURRENT_NLP_REQUEST_V1',run_id=run_id,method=METHOD,input_sha256=clean['input_sha256'],origin_native=k,origin_sim_time=clean['sim_time'],case=dict(pose=clean['pose'],gear=clean['gear'],nominal=clean['nominal_twist'],causal=clean['causal'],sim_time=clean['sim_time']),public_known=known,model_identity='EXPLICIT_IDEAL_KINEMATIC_ONLY',physical_authority=False)
 request['request_sha256']=digest(request);return dict(current=clean,request=request)
