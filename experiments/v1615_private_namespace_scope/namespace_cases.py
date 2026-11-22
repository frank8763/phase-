"""New canonical/private alias ownership only; SOFTWARE, no definitions import."""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import types

def run(c,source,target,save,refused):
    before=c.R/'experiments/v1612_locked_writer_census'
    changed={'namespace_scope.py','transaction.py','components.py','current_reserve.py',
             'common.py','entry.py','source_target.py'}
    reuse=[]
    for p in before.glob('*.py'):
        if p.name in changed:continue
        current=c.C/p.name
        normalized=current.read_text().replace(c.C.name,before.name).replace('v1615','v1612')
        assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(p.read_text())),p.name
        reuse.append(dict(name=p.name,prior_sha256=c.sha(p),current_sha256=c.sha(current)))
    # Read the original explicit collision-name declaration without importing
    # that old loader or its definitions/model dependencies again.
    original=c.R/'experiments/v1530_explicit_we_private_binding/definitions.py'
    tree=ast.parse(original.read_text())
    assigns={n.targets[0].id:n.value for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
    files=ast.literal_eval(assigns['FILES']);private=ast.literal_eval(assigns['PRIVATE_NAMES'])
    expression=assigns['COLLISION_NAMES']
    assert isinstance(expression,ast.BinOp)and isinstance(expression.op,ast.Add)
    extra=ast.literal_eval(expression.right)
    names=tuple(k for k in files if k!='resource_policy')+private+extra
    assert len(set(names))==len(names)
    definitions=types.SimpleNamespace(COLLISION_NAMES=names)
    ns=c.load('v1615_software_namespace_scope',c.C/'namespace_scope.py')
    source_file=str(c.C/'namespace_scope.py')
    def module(label):
        value=types.ModuleType(label);value.__file__=source_file
        value.SOFTWARE_ONLY=True;value.resident_globals={'control_memory_token':'UNCHANGED','plant_state_token':'UNCHANGED'}
        return value
    missing=object();baseline={name:sys.modules.get(name,missing)for name in names}
    assert ns.MARKER not in sys.modules
    actual={name:module('SOFTWARE_ACTUAL_'+name)for name in ('common','kernel','factory')}
    for name in names:sys.modules.pop(name,None)
    sys.modules.update(actual)
    path_before=list(sys.path)
    def pristine():
        for name in names:sys.modules.pop(name,None)
        sys.modules.update(actual);sys.modules.pop(ns.MARKER,None);sys.path[:]=path_before
    def current_restored():
        assert all(sys.modules.get(n)is m for n,m in actual.items())
        assert all(n in actual or n not in sys.modules for n in names)
        assert sys.path==path_before
        assert all(m.resident_globals=={'control_memory_token':'UNCHANGED','plant_state_token':'UNCHANGED'}for m in actual.values())
    proof={}
    try:
        bank=ns.Bank(source=source,definitions=definitions)
        with bank.activate():
            assert all(name not in sys.modules for name in names)
            fresh=module('SOFTWARE_PRIVATE_COMMON');sys.modules['common']=fresh
            sys.path.insert(0,'SOFTWARE_SCOPED_PATH')
            with bank.activate():assert sys.modules['common']is fresh
        current_restored();assert ns.MARKER not in sys.modules
        with bank.activate():assert sys.modules['common']is fresh
        current_restored();proof['normal_reentrant_and_second_callback']=bank.proof()
        bank=ns.Bank(source=source,definitions=definitions)
        first=RuntimeError('SOFTWARE_PRIVATE_FIRST')
        try:
            with bank.activate():
                sys.modules['common']=module('SOFTWARE_PRIVATE_FAIL');raise first
        except RuntimeError as error:assert error is first
        else:raise AssertionError('SOFTWARE_FIRST_ERROR_LOST')
        current_restored();assert bank.failed and bank.last_restore_verified
        refused('no_retry_after_private_exception',lambda:enter(bank))
        proof['first_exception_restored_actual_objects']=True
        # Namespace proof failure and marker ownership failure are independent
        # of actual alias/path restoration, and cannot replace the first error.
        bank=ns.Bank(source=source,definitions=definitions)
        first=RuntimeError('SOFTWARE_FIRST_WITH_SECONDARY')
        try:
            with bank.activate():
                bad=module('SOFTWARE_UNDECLARED_PRIVATE');bad.__file__=str(c.R/'experiments/UNDECLARED.py')
                sys.modules['common']=bad;sys.modules[ns.MARKER]=module('SOFTWARE_FOREIGN_MARKER')
                sys.path.insert(0,'SOFTWARE_PATH_REQUIRES_RESTORE');raise first
        except RuntimeError as error:
            assert error is first and getattr(error,'secondary',None)and getattr(error,'secondary_namespace_restore',None)
        current_restored();assert bank.failed and not bank.last_restore_verified
        sys.modules.pop(ns.MARKER,None)
        proof['first_and_two_secondary_errors_preserved']=True
        bank=ns.Bank(source=source,definitions=definitions)
        def nested_poison():
            with bank.activate():
                try:
                    with bank.activate():raise RuntimeError('SOFTWARE_NESTED_FIRST')
                except RuntimeError:pass
        refused('nested_caught_error_still_poisoned',nested_poison)
        current_restored();assert bank.failed
        bad_source=dict(source);bad_source[str((c.C/'namespace_scope.py').relative_to(c.R))]='0'*64
        refused('resident_source_SHA_changed',lambda:ns.Bank(source=bad_source,definitions=definitions))
        unknown=module('SOFTWARE_UNKNOWN');unknown.__file__=str(c.R/'experiments/UNREGISTERED.py')
        sys.modules['common']=unknown
        refused('unregistered_resident_source',lambda:ns.Bank(source=source,definitions=definitions));pristine()
        bank=ns.Bank(source=source,definitions=definitions);bank.owner=(os.getpid()+100000,bank.owner[1])
        refused('foreign_owner',lambda:enter(bank));current_restored()
        bank=ns.Bank(source=source,definitions=definitions);sys.modules['common']=module('SOFTWARE_CHANGED_OBJECT')
        refused('resident_object_replaced',lambda:enter(bank));pristine()
        sys.modules[ns.MARKER]=module('SOFTWARE_ACTIVE_OTHER_BANK')
        refused('other_bank_active',lambda:ns.Bank(source=source,definitions=definitions));pristine()

        # Execute the real new transaction through its binding/close seam.
        # All model-bearing interfaces are explicit SOFTWARE stubs; the old
        # loader, geometry, policy, constructors and physics are never called.
        transaction=c.load('v1615_real_transaction_source_path',c.C/'transaction.py')
        folder=target/'SOFTWARE_TRANSACTION';folder.mkdir();save(folder/'GOAL_BOUND_PRIVATE_ADMISSION.json',{'SOFTWARE_ONLY':True})
        class Guard:
            def __init__(self,**kwargs):
                self.authority=dict(boot_id='SOFTWARE_BOOT',absolute_deadline_unix=1795395600,hard_stop_monotonic=1.)
            def counts(self):return dict(models=0,native=0,physical_native=0,replay_native=0,inflight_unknown=False)
        called=[]
        def software_loader(prepared,*,authority,lock):
            assert all(n not in sys.modules for n in names)
            assert authority['models_authorized']is False and authority['method_origin_authorized']is False
            sys.modules['common']=module('SOFTWARE_TRANSACTION_PRIVATE')
            called.append('COLD_BINDING_SOFTWARE_ONLY')
            return {},dict(passed=True,SOFTWARE_ONLY=True,models=0)
        fake_definitions=types.SimpleNamespace(COLLISION_NAMES=names,load_definitions=software_loader)
        class StopAtScope:
            def __init__(self,**kwargs):raise RuntimeError('SOFTWARE_POST_BINDING_FIRST')
        original_load=transaction.load
        def supplied(label,path,prepared):
            if path.name=='capability.py':return types.SimpleNamespace(Guard=Guard)
            if path.name=='definitions.py':return fake_definitions
            if path.name=='namespace_scope.py':return ns
            if path.name=='scoped_output.py':return types.SimpleNamespace(Scope=StopAtScope)
            return types.SimpleNamespace(SOFTWARE_ONLY=True)
        transaction.load=supplied
        try:
            answer=transaction.execute(output=folder,source_owner=None,method={'SOFTWARE_ONLY':True},setup={},source=source,lock=None,
                save_result=lambda value:save(folder/'TRANSACTION_RESULT.json',value))
        finally:transaction.load=original_load
        assert called==['COLD_BINDING_SOFTWARE_ONLY']and not answer['passed']and answer['closed']
        assert answer['first_error']=="RuntimeError('SOFTWARE_POST_BINDING_FIRST')"and answer['secondary_errors']==[]
        assert answer['definition_namespace']['canonical_resident_objects_restored']
        current_restored()

        # The real callback wrapper must save a namespace-before-model error
        # once and refuse further use; this creates no reserve or model arrays.
        reserve=c.load('v1615_real_current_wrapper',c.C/'current_reserve.py')
        value=reserve.CurrentReserve.__new__(reserve.CurrentReserve)
        bank=ns.Bank(source=source,definitions=definitions);bank.owner=(os.getpid()+100000,bank.owner[1])
        value.namespace_bank=bank;value.failed=False;value.in_call=False;value.guard=Guard();saved=[]
        value.save_partial=lambda proof,arrays:saved.append((proof,arrays))
        refused('current_namespace_before_model',lambda:value({'SOFTWARE_PACKET':True},{}))
        assert value.failed and len(saved)==1 and saved[0][0]['namespace_rejected_before_model']and saved[0][1]is None
        refused('current_namespace_no_retry',lambda:value({'SOFTWARE_PACKET':True},{}))
        assert len(saved)==1
        save(target/'SOFTWARE_CURRENT_NAMESPACE_PARTIAL.json',dict(passed=True,partial=saved[0][0],models=0,actual_runtime_qualified=False))
        # The guard below is a source predicate, not a numeric current stop.
        transaction_tree=ast.parse((c.C/'transaction.py').read_text())
        function=next(n for n in transaction_tree.body if isinstance(n,ast.FunctionDef)and n.name=='execute')
        handler=next(n for n in function.body if isinstance(n,ast.Try)).handlers[0]
        assert ast.unparse(handler.body[0])=="result['passed'] = False"
        component=(c.C/'components.py').read_text()
        assert "with context['namespace_bank'].activate():"in component and "CurrentReserve(namespace_bank=context['namespace_bank']"in component
        proof.update(production_transaction_binding_exception_saved=True,production_current_wrapper_partial_once=True,
            original_loader_import_or_numerics_executed=False,all_canonical_fixture_objects_and_globals_restored=True)
        save(target/'NAMESPACE_OWNERSHIP_PROOF.json',dict(passed=True,SOFTWARE_ONLY=True,proof=proof,old_loader_source_sha256=c.sha(original),
            old_loader_checks_unchanged=True,original_collision_names=names,unchanged_source_modules=reuse,
            models=0,actual_capture_qualified=False,actual_runtime_qualified=False,whole_route_passed=False))
        return dict(namespace_ownership_source_only=True,new_namespace_proof=proof,unchanged_modules=len(reuse),
            actual_runtime_qualified=False,model_or_current2200_runtime_qualified=False,models=0,physical_native=0)
    finally:
        for name in names:sys.modules.pop(name,None)
        for name,value in baseline.items():
            if value is not missing:sys.modules[name]=value
        sys.modules.pop(ns.MARKER,None);sys.path[:]=path_before

def enter(bank):
    with bank.activate():pass
