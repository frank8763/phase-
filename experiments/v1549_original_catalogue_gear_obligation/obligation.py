"""Conditional source proof of raw-template/canonical-gear incompatibility.

No policy execution, model constructor, physical step or future measurement.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
GEAR='experiments/v1396_rpp_rpc_retirement/gear_handoff.py'
ROWS='runs/v1144_saved_entry_relay/software/ROWS.json'
METHOD='runs/v1532_observer_epoch_origin/source_target/METHOD_INPUT.json'
CATALOGUE='experiments/v1221_exact_stop_pruning/candidate_observer.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def node(text):return ast.parse(text).body[0]
def checked(name,prepared):
    p=R/name;assert p.resolve()==p and not p.is_symlink()and p.is_file()and p.stat().st_size<=1024**2
    assert prepared[name]==sha(p),'CATALOGUE_GEAR_SOURCE_CHANGED';return p
class ObligationRefusal(AssertionError):
    def __init__(self,first,proof,secondary=None):super().__init__(first);self.proof=proof;self.secondary=secondary

def prove(*,prepared_sources,save_proof):
    proof=dict(passed=False,models=0,new_analytical_native=0,physical_native=0,
               source_conditional_only=True,model_permission=False,physical_permission=False,
               freshwire=False,actual_response_tested=False,original_catalogue_modified=False)
    first=None;answer=None
    try:
        paths={name:checked(name,prepared_sources)for name in [GEAR,ROWS,METHOD,CATALOGUE]}
        method=json.loads(paths[METHOD].read_text());clean=copy.deepcopy(method);identity=clean.pop('method_input_sha256');assert digest(clean)==identity
        assert method['not_fresh_wire']and method['physical_permission']is False
        packet=method['physical_source']['packet'];memory=method['physical_source']['gear_memory']
        assert set(memory)=={'gear','brake_start','last_tick'}and memory['last_tick']==method['fixed_origin_native']-1
        assert memory['gear']==1 and memory['brake_start']is None,'CURRENT_SAVED_GEAR_OUTSIDE_CONDITIONAL_PROOF'
        assert packet['native_tick']==method['fixed_origin_native']and abs(packet['sim_time']-method['fixed_origin_sim_time'])<=1e-8
        tree=ast.parse(paths[GEAR].read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='GearHandoff');f=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='select')
        # Exact source statements establish the implication without running
        # the policy on inventedfuturefeedback or consuming a native step.
        assignments={n.targets[0].id:n for n in f.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
        for name,text in [('wanted','wanted = 0 if abs(v) < .005 else sign(v, 0.)'),
                          ('opposing','opposing = wanted and any(g and g != wanted for g in [self.gear, drive_gear, body_gear])'),
                          ('reverse_reentry','reverse_reentry = bool(wanted < 0 and drive_gear == 0 and abs(body[3]) > BODY_REST)')]:
            assert ast.dump(assignments[name])==ast.dump(node(text)),'ORIGINAL_GEAR_BRANCH_SOURCE_CHANGED:'+name
        begin=node('if self.brake_start is None and (opposing or reverse_reentry):\n self.brake_start = native_tick')
        assert any(ast.dump(n)==ast.dump(begin)for n in f.body)
        brake=next(n for n in f.body if isinstance(n,ast.If)and ast.dump(n.test)==ast.dump(ast.parse('self.brake_start is not None',mode='eval').body))
        hold=node('if native_tick-self.brake_start < BRAKE_NATIVE or not resting:\n return 0.,0.,dict(proof,mode="GEAR_BRAKE_HOLD",released=False)')
        assert ast.dump(brake.body[0])==ast.dump(hold)
        constant=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='BRAKE_NATIVE'for t in n.targets));assert ast.literal_eval(constant.value)==200
        gear_writes=[n for n in ast.walk(f)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Attribute)and isinstance(t.value,ast.Name)and t.value.id=='self'and t.attr=='gear'for t in n.targets)]
        assert len(gear_writes)==2 and all(isinstance(n.value,ast.Name)and n.value.id=='wanted'for n in gear_writes)
        rows=json.loads(paths[ROWS].read_text())['rows'];offset=0;first_signed=None
        for row in rows:
            assert len(row)==4 and type(row[2])is int and row[2]>0 and all(math.isfinite(float(x))for x in row)
            if abs(row[1])>=.005:first_signed=dict(offset_native=offset,requested_speed=float(row[1]),parked=bool(row[3]));break
            assert row[1]==0.,'LEADING_NONZERO_SUBTHRESHOLD_REQUEST_UNMAPPED';offset+=row[2]
        assert first_signed is not None and first_signed['requested_speed']<-.005 and not first_signed['parked']
        catalogue=ast.parse(paths[CATALOGUE].read_text());syn=next(n for n in catalogue.body if isinstance(n,ast.FunctionDef)and n.name=='_synthesize')
        initial=next(n for n in syn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='catalog'for t in n.targets));assert ast.literal_eval(initial.value.left)==[(0.,0)]
        cuts=ast.literal_eval(next(n for n in ast.walk(syn)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='cut').iter);assert cuts==[11400,11800]and all(cut>offset for cut in cuts)
        proof.update(passed=True,method_input_sha256=identity,saved_gear=copy.deepcopy(memory),
            saved_gear_not_new_independent_recomputation=True,first_original_template_signed_request=first_signed,
            known_conditional_base_catalogue_indices=[0,1],other40cases_unknown_without_response_history=True,
            premise='all preceding zero requests accepted with finitevalidfeedback; otherwise trace alreadyrefused',
            induction='wanted0 -> opposingfalse/reverse_reentryfalse/brakeNone -> gear1remains/no transitionclock',
            first_opposing_request_result='sets brake_start=currentnative; elapsed0<200 ->appliedv=w=0 regardlessrest',
            raw_versus_filtered_controls_identical=False,canonical_brake_native=200,
            actual_transition_release_and_rest_unknown=True,no_virtual_future_feedback_used=True,
            source_SHA={name:sha(p)for name,p in paths.items()},
            gear_select_AST_sha256=hashlib.sha256(ast.dump(f).encode()).hexdigest(),
            no_new_model_or_policy_execution=True)
        answer=copy.deepcopy(proof)
    except BaseException as error:first=repr(error);proof.update(passed=False,first_error=first)
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error);proof['passed']=False
    if first or secondary:raise ObligationRefusal(first or'CATALOGUE_GEAR_PROOF_SAVE_FAILED',proof,secondary)
    return answer
