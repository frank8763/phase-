"""Necessary new2200scope/source qualification; no model or array execution."""
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1540_source_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def expected_source(name,text):
    if name in ['records.py','generate.py','audit.py','stop_checks.py','contract.py','owner.py']:
        text=re.sub(r'\b201\b','2201',text);text=re.sub(r'\b200\b','2200',text)
        text=text.replace('CPP200','CPP2200').replace('Python200','Python2200')
    if name in ['contract.py','driver.py','owner.py','origin.py']:
        text=text.replace('CURRENT_ORIGIN_COMPLETE_STOP_COMPONENT','CURRENT_ORIGIN_COMPLETE_ORIGINAL2200_STOP_COMPONENT')
    if name in ['contract.py','owner.py']:
        text=text.replace('==8','==9').replace('scientific_revision=8','scientific_revision=9').replace('science_revision=8','science_revision=9')
    if name=='origin.py':text=text.replace("=='v1536_review_precharge_source'","=='v1540_original_stop_horizon'")
    if name=='common.py':text=text.replace("BASE=R/'runs/v1532_observer_epoch_origin/SOURCE_FREEZE.json'","BASE=R/'runs/v1539_original_observer_response_seam/SOURCE_FREEZE.json'")
    if name=='stop_checks.py':text=text.replace('checks=dict(full200=len(u)==2200 and len(s)==len(u)+1,','checks=dict(full_original2200=len(u)==2200 and len(s)==len(u)+1,minimum200_preserved=len(u)>=200,')
    if name=='records.py':text=text.replace('scientific_revision=8','method_epoch_revision=8,scientific_integration_revision=9')
    return text

def main():
    start=time.monotonic();assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models=0),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,phase_FFI_loads=0)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','vehicle','factory','runtime','bindings','kernel','prediction','coupled_model'}:
                raise AssertionError('STOP2200_SOURCE_METADATA_ONLY:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            p=Path(frame.f_code.co_filename)
            if p.is_absolute()and p.is_relative_to(c.R)and frame.f_code.co_name in {'__init__','step','compute','simulate','expand','predict'}:
                if not p.is_relative_to(C)and p not in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}:raise AssertionError('STOP2200_SOURCE_NO_NUMERIC_CALL')
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']and parent['scientific_revisions']==9
            source=c.read(c.BASE)['files'].copy();assert all(c.sha(c.R/n)==h for n,h in source.items())
            prior=c.R/'runs/v1536_review_precharge_source';old=c.R/'experiments/v1536_review_precharge_source'
            assert c.read(prior/'COMPLETION.json')['passed']and c.read(prior/'ENTRY_QUALIFICATION.json')['passed']
            registration=c.read(c.O/'SCIENTIFIC_REVISION_REGISTRATION.json');assert registration['scientific_integration_revision']==9 and registration['registered_before_method_implementation']and registration['horizon_native']==2200
            assert registration['immutable_base_method_file_sha256']==c.sha(c.INPUT)
            unchanged={}
            for name in ['records.py','generate.py','audit.py','stop_checks.py','contract.py','driver.py','owner.py','origin.py','common.py']:
                expected=ast.dump(ast.parse(expected_source(name,(old/name).read_text())))
                assert ast.dump(ast.parse((C/name).read_text()))==expected,'UNDECLARED_NUMERICAL_OR_CONTROL_SOURCE_CHANGE:'+name
                unchanged[name]=dict(old_sha256=c.sha(old/name),new_sha256=c.sha(C/name),only_declared_horizon_scope_or_version_change=True)
            limits=c.limits();previous=c.read(old/'LIMITS.json');previous.update(scope='CURRENT_ORIGIN_COMPLETE_ORIGINAL2200_STOP_COMPONENT',scientific_revision=9,generation_native=2200,success_only_audit_native=2200,original_stop_native=2200);assert limits==previous
            original=c.R/registration['original_stop_source'];assert c.sha(original)==registration['original_stop_source_sha256']==source[registration['original_stop_source']]
            tree=ast.parse(original.read_text());body=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='prove')
            tuples=[n for n in ast.walk(body)if isinstance(n,ast.Tuple)and len(n.elts)==4 and all(isinstance(v,ast.Constant)for v in n.elts)]
            assert sum([v.value for v in n.elts]==[0.,0.,2200,0]for n in tuples)==2
            contract=c.load('v1540_real_contract',C/'contract.py');owner=c.load('v1540_real_owner',C/'owner.py')
            # Explicit software metadata only: no2200trajectory or model is made.
            now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            p=dict(active_round=C.name,models_now_authorized=True,active_math_round=None,scientific_revisions=9,hard_stop_monotonic=mono+120)
            authority=dict(scope=limits['scope'],models_authorized=True,physical_authorized=False,optimizer_authorized=False,
                           round_id=C.name,scientific_revision=9,boot_id=boot,source_manifest_sha256='a'*64,current_input_sha256='b'*64,
                           absolute_deadline_unix=now+60,hard_stop_monotonic=mono+60)
            for key in ['generation_native','success_only_audit_native','maximum_nominal_native','model_writer_bytes','parent_writer_bytes']:authority[key]=limits[key]
            assert contract.validate(authority,parent=p,limits=limits,boot=boot,now_unix=now,now_mono=mono,source_identity='a'*64,input_sha='b'*64)
            cases=[]
            for key,new in [('scope','CURRENT_ORIGIN_COMPLETE_STOP_COMPONENT'),('generation_native',200),('success_only_audit_native',200),('scientific_revision',8)]:
                wrong=copy.deepcopy(authority);wrong[key]=new
                try:contract.validate(wrong,parent=p,limits=limits,boot=boot,now_unix=now,now_mono=mono,source_identity='a'*64,input_sha='b'*64)
                except AssertionError:cases.append(dict(field=key,rejected=True))
                else:raise AssertionError('STOP2200_SCOPE_NEGATIVE_ACCEPTED:'+key)
            gen=dict(passed=True,closed=True,analytical_native=2200,analytical_inflight_unknown=False);receipt=dict(complete=True,native=2200)
            assert contract.audit_allowed(gen,receipt)
            for field in ['analytical_native','passed','analytical_inflight_unknown']:
                wrong=gen.copy();wrong[field]={'analytical_native':200,'passed':False,'analytical_inflight_unknown':True}[field];assert not contract.audit_allowed(wrong,receipt);cases.append(dict(audit_dependency_field=field,rejected=True))
            good=dict(closed=True,passed=True,first_error=None,secondary_errors=[],generation_inflight_unknown=False,audit_inflight_unknown=False,generation_analytical_native=2200,audit_analytical_native=2200,cpp_engine_constructions=1,python_predictor_constructions=1,physical_native=0,ownreplay_native=0,optimizer_calls=0,nominal_native=0)
            assert owner.runtime_passed(0,good,[])
            for value in [200,2199,2201,2200.]:
                wrong=good.copy();wrong['audit_analytical_native']=value;assert not owner.runtime_passed(0,wrong,[]);cases.append(dict(owner_audit_native_repr=repr(value),rejected=True))
            # New production CLI refuses before definitions/model construction.
            driver=c.load('v1540_real_driver',C/'driver.py');closed=driver.execute()
            assert closed['closed']and not closed['passed']and 'CURRENT_ORIGIN_STOP_COMPONENT_NOT_ADMITTED'in closed['first_error']
            assert closed['generation_analytical_native']==closed['audit_analytical_native']==closed['cpp_engine_constructions']==closed['python_predictor_constructions']==0
            fixed=c.read(prior/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',fixed);assert c.sha(c.INPUT)==fixed['method_input_file_sha256']
            # Parent serialization/precharge function bodies exact; prior real
            #963327Bprecharge/origin/byte proofs reused without rerunning suites.
            trees=[ast.parse((root/'owner.py').read_text())for root in [old,C]]
            for name in ['parent_bytes','reserve_parent_budget']:
                assert ast.dump(next(n for n in trees[0].body if isinstance(n,ast.FunctionDef)and n.name==name))==ast.dump(next(n for n in trees[1].body if isinstance(n,ast.FunctionDef)and n.name==name))
            assert len(owner.parent_bytes(parent))+8192<=131072
            proof=dict(passed=True,models=0,source_transforms=unchanged,new_scope_negative_cases=cases,software2200_metadata_not_model_work=True,
                       unadmitted_real_CLI_saved_before_numerical_binding=True,original_stop_source_AST_only=True,
                       original_input_bytes_unchanged=True,prior_origin_API_proof_sha256=c.sha(c.R/'runs/v1532_observer_epoch_origin/ORIGIN_API_QUALIFICATION.json'),
                       prior_precharge_proof_sha256=c.sha(prior/'CLOSURE_QUALIFICATION.json'),old_definition_origin_OS_ROS_serializer_model_suites_not_rerun=True)
            c.put(c.O/'HORIZON_SOURCE_QUALIFICATION.json',proof)
            for path in C.iterdir():
                if path.is_file():source[str(path.relative_to(c.R))]=c.sha(path)
            for path in [c.O/'SCIENTIFIC_REVISION_REGISTRATION.json',c.O/'FIXED_INPUTS.json',prior/'CLOSURE_QUALIFICATION.json',prior/'COMPLETION.json',c.O/'unadmitted/RESULT.json']:
                source[str(path.relative_to(c.R))]=c.sha(path)
            assert all(c.sha(c.R/n)==h for n,h in source.items())
            c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,numerical_2200_component_qualified=False),maximum=4*1024**2)
            result.update(passed=True,bootstrap=bootstrap,source_frozen=True,new_scope_negative_cases=len(cases),prior_proofs_SHA_reused=True,original2200_numeric_executed=False)
    except BaseException as error:result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
