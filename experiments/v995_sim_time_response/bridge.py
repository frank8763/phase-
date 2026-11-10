"""Full sim-time versus previous wall-paced held-angle equivalence, zero models."""
import gzip,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];BASE=R/'runs/v995_sim_time_response/bridge_v993'
def read(p):return json.loads(p.read_text())
def canonical(setup):
    setup=json.loads(json.dumps(setup));certificate=setup['actor']['swept_envelope_reference'];certificate.pop('elapsed_s',None);certificate['search'].pop('wall_s',None)
    return setup
def compare(out):
    out=Path(out);errors={};equal_lengths=True
    with np.load(BASE/'physics/NATIVE_TRACE.npz')as a,np.load(out/'physics/NATIVE_TRACE.npz')as b:
        assert a.files==b.files,'TRACE_FIELDS_CHANGED'
        for k in a.files:
            if a[k].shape!=b[k].shape:equal_lengths=False;errors[k]=None
            else:errors[k]=float(np.max(abs(a[k]-b[k])))if a[k].size else 0.
    initials=[np.load(p/'physics/INITIAL_STATE.npz')['state']for p in [BASE,out]]
    initial_error=float(abs(initials[0]-initials[1]).max())if initials[0].shape==initials[1].shape else None
    setups=[canonical(read(p/'physics/SETUP.json'))for p in [BASE,out]]
    commands=[read(p/'physics/BODY_COMMANDS.json')for p in [BASE,out]]
    controls_equal=len(commands[0])==len(commands[1])and all(x[1:]==y[1:]for x,y in zip(*commands))
    contacts=[json.loads(gzip.decompress((p/'physics/CONTACTS.json.gz').read_bytes()))for p in [BASE,out]]
    sensors=[json.loads(gzip.decompress((p/'physics/SENSORS.json.gz').read_bytes()))for p in [BASE,out]]
    n=[read(p/'RESULT.json')for p in [BASE,out]]
    checks=dict(equal_trace_lengths=equal_lengths,all_trace_arrays_exact=all(x is not None and x<=1e-8 for x in errors.values()),
        same_complete_physical_setup=setups[0]==setups[1],same_initial_state=initial_error is not None and initial_error<=1e-8,
        same_control_inputs_and_feedback=controls_equal,same_contacts=contacts[0]==contacts[1],same_sensor_packets=sensors[0]==sensors[1],
        same_discovery=n[0]['native']['first_actor_detection']==n[1]['native']['first_actor_detection'],both_own_replays_passed=all(x['replay']['passed']for x in n))
    result=dict(passed=all(checks.values()),checks=checks,trace_errors=errors,initial_error=initial_error,models=0,
        ignored_construction_clocks_only=['actor.swept_envelope_reference.elapsed_s','actor.swept_envelope_reference.search.wall_s'],
        wall_clock_timestamps_in_body_commands_ignored=True,real_time_qualified=False)
    (out/'CLOCK_EQUIVALENCE.json').write_text(json.dumps(result,indent=2)+'\n');return result
