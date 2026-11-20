"""Use the qualified bounded storage transport for the first V1383 delivery."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;P=R/'runs'/C.name

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Transport:
    def __init__(self,folder):
        assert folder.parent==R/'runs' and folder.name=='v1383_exact_timed_handoff'
        self.folder=folder;self.tag='phase-'+folder.name.replace('_','-')+'-20261120'
        self.helper=load('bounded_round_transport',R/'experiments/v1389_idempotent_storage_transfer/resume.py')
        self.helper.O=P;self.helper.W=folder;self.helper.base.TAG=self.tag

    def gh(self,args,output=None,timeout=300):
        h=self.helper
        if args[:2]==['release','upload']:
            assert args[2]==self.tag and output is None
            path=Path(args[3]);h.ensure_uploaded(path,h.assets(h.read(self.folder/'RELEASE.json')));return ''
        if args[:2]==['release','download']:
            assert args[2]==self.tag and args[-2:]==['--output','-']
            name=args[args.index('--pattern')+1];assert Path(name).name==name
            row=h.assets(h.read(self.folder/'RELEASE.json'))[name]
            if output is not None:path=Path(output.name)
            else:
                directory=P/'metadata_readback';directory.mkdir(exist_ok=True);path=directory/name
            h.download(path,row)
            return None if output is not None else path.read_text()
        if args[:1]==['api']:
            if '--method' not in args:return h.base.gh(args,timeout=timeout,output=output)
            assert args[:3]==['api','--method','POST'] and args[3]=='repos/frank8763/phase-/releases'
            try:return h.base.gh(args,timeout=timeout,output=output)
            except (AssertionError,TimeoutError):
                # Reconcile an unknown create result once; never issue a second
                # create POST when a release might already exist.
                return h.base.gh(['api','repos/frank8763/phase-/releases/tags/'+self.tag],timeout=90)
        raise AssertionError('UNREGISTERED_DELIVERY_OPERATION')

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    helper=load('delivery_evidence_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
    assert helper.read(P/'QUALIFICATION.json')['passed'] and not (P/'CLAIM.json').exists()
    assert all(helper.sha(R/name)==h for name,h in helper.read(P/'SOURCE_FREEZE.json')['files'].items())
    folder=R/'runs/v1383_exact_timed_handoff';assert not (folder/'DELIVERY_CLAIM.json').exists()
    helper.dump(P/'CLAIM.json',dict(started_unix=time.time(),models=0,original_delivery_first_invocation=True))
    original=load('original_closed_round_delivery',R/'experiments/v1382_weekend_campaign/deliver_round.py')
    transport=Transport(folder);original.gh=transport.gh;sys.argv=[str(C/'deliver.py'),str(folder.relative_to(R))]
    original.main()
    helper.dump(P/'FINALIZED.json',dict(passed=True,models=0,original_scientific_source_unchanged=True,full_remote_proof=str((folder/'FULL_REMOTE_VERIFIED.json').relative_to(R))))

if __name__=='__main__':main()
