from pathlib import Path
import copy, hashlib, importlib.util, json, os, time

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs'/C.name

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def freeze(p):
    value=read(p)
    inherited=freeze(R/value['inherit_freeze_path'])if'inherit_freeze_path'in value else{}
    assert not'inherit_freeze_path'in value or sha(R/value['inherit_freeze_path'])==value['inherit_freeze_sha256']
    assert all(n not in inherited or inherited[n]==h for n,h in value['files'].items())
    return dict(inherited,**value['files'])

def main():
    os.sched_setaffinity(0,{7});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    O.mkdir(exist_ok=True);assert not(O/'ONCE.json').exists()
    (O/'ONCE.json').write_text(json.dumps(dict(pid=os.getpid(),unix=time.time(),models=0)))
    S=R/'runs/v2064_five_algorithm_parallel_math'
    current=read(S/'CURRENT_INPUT.json');proposal=read(S/'priest_output/POLYNOMIAL_PROPOSAL.json')['candidate']
    source=freeze(S/'SOURCE_FREEZE.json');api=load('new_PRIEST_origin_control',C/'interface.py')
    prior=read(R/'runs/v2068_priest_t0_command_domain/RESULT.json')['report']
    pins={str(p.relative_to(R)):sha(p)for p in [C/'interface.py',C/'qualify_software.py',S/'CURRENT_INPUT.json',S/'priest_output/POLYNOMIAL_PROPOSAL.json',R/'runs/v2068_priest_t0_command_domain/RESULT.json']}
    checked=[]
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError,KeyError):checked.append(name)
        else:raise AssertionError('EXPECTED_SAFETY_REFUSAL:'+name)
    def controller(c=None,p=None,s=None):
        return api.OriginPreview(c or current,p or proposal,s or source,archived_software_only=True)
    control=controller();answer=control.preview(current['origin'])
    assert answer['raw_request']==prior['first_original_preview_request']
    assert answer['actual_execution_permitted']is False
    reject('repeat_origin',lambda:control.preview(current['origin']))
    closed=controller();closed.close();reject('closed',lambda:closed.preview(current['origin']))
    reject('archived_input_production',lambda:api.OriginPreview(current,proposal,source))
    changed=copy.deepcopy(source);changed['experiments/v1485_priest_current_polynomial_seam/polynomial.py']='0'*64
    reject('changed_original_source',lambda:controller(s=changed))
    changed=copy.deepcopy(current['origin']);changed['body'][0]+=.001
    reject('foreign_measured_packet',lambda:controller().preview(changed))
    changed=copy.deepcopy(current['origin']);changed['native_tick']+=1;changed['sim_time']+=.01
    reject('different_clock',lambda:controller().preview(changed))
    changed=copy.deepcopy(proposal);changed['reply']['coefficients_x'][0]+=.001
    reject('different_polynomial',lambda:controller(p=changed))
    changed=copy.deepcopy(proposal);changed['reply']['coefficients_x'][4]=100.
    # Rebind the deliberately invalid reference as a software-only fixture;
    # actual current input and optimizer output remain untouched.
    changed=api.load('original_candidate_fixture',api.OLD/'candidate_output.py').bind(current,changed['reply'])
    reject('raw_twist_domain',lambda:controller(p=changed).preview(current['origin']))
    assert all(sha(R/n)==h for n,h in pins.items())
    value=dict(closed=True,software_passed=True,negative_cases=checked,saved_origin_preview=answer,input_hashes=pins,models=0,optimizer_calls=0,physics=0,replay=0,formal_slots=0,current_live_vehicle_qualified=False,full_response_qualified=False,no_saved_control_installed_in_new_plant=True)
    raw=json.dumps(value,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<128*1024
    (O/'RESULT.json').write_text(raw);print(json.dumps(value))

if __name__=='__main__':main()
