"""Compare public metadata only; independently validate private actuator schema."""
import math

def check_setup(setup,meta):
 assert set(meta['setup'])=={'known','limits','slew_per_second'},'PUBLIC_METADATA_SCHEMA_CHANGED'
 for key in ['known','limits','slew_per_second']:assert setup[key]==meta['setup'][key],'ORIGINAL_PUBLIC_MODEL_CONTRACT_CHANGED '+key
 assert abs(setup['dt']-.01)<=1e-12,'ORIGINAL_NATIVE_TIMESTEP_CHANGED'
 ids=setup['actuator_ids'];assert len(ids)==4 and len(set(ids))==4 and all(type(x)is int and x>=0 for x in ids),'INVALID_ACTUATOR_IDS'
 assert len(setup['steering_qpos_addresses'])==len(setup['steering_qvel_addresses'])==2,'INVALID_STEERING_ADDRESSES'
 assert len(setup['limits'])==len(setup['slew_per_second'])==4 and all(math.isfinite(v)for row in setup['limits']for v in row),'INVALID_PHYSICAL_CONTROL_CONTRACT'
 return True
