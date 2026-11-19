"""Run real zero-model local closure in an isolated fake evidence root."""
import importlib.util
import json
from pathlib import Path
import tempfile
from component_context import R,C,O,dump


def main():
    with tempfile.TemporaryDirectory(dir=O) as directory:
        root=Path(directory);source=root/'experiments/mock';out=root/'runs/mock';source.mkdir(parents=True);out.mkdir(parents=True)
        (root/'runs/v648_static_unknown').mkdir();(root/'docs').mkdir()
        (root/'REVIEW_PENDING').write_bytes(b'preserved-review\n');(out/'REVIEW_PENDING.before').write_bytes(b'preserved-review\n')
        (source/'CAMPAIGN_CONFIG.json').write_text(json.dumps({'storage_limit_bytes':10*1024**3}));(source/'TASKS.json').write_text('[]\n');(source/'MOCK_SOURCE.txt').write_text('source archive qualification only\n')
        summary=dict(closed=True,results=[],unexecuted=['never_executed'],skipped_dependencies=[],passed=False,stop_reason='MOCK_ALL_BRANCHES_UNEXECUTED')
        (out/'COMPLETION.json').write_text(json.dumps(summary));(out/'ROUND_WINDOW.json').write_text(json.dumps({'absolute_deadline_unix':1795050000.}))
        spec=importlib.util.spec_from_file_location('actual_offline_finalizer',C/'finalize.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.R=root;module.C=source;module.O=out;module.RAW=root/'runs/raw';module.sources=lambda:True
        module.main()
        final=json.loads((out/'FINALIZED.json').read_text());index=json.loads((out/'OFFLINE_ARCHIVE_INDEX.json').read_text())
        assert final['passed'] and not final['scientific_branch_passed'] and final['models']==0
        assert index['local_all_members_SHA_verified'] and not index['raw_deleted'] and not index['remote_verified']
        assert (root/'REVIEW_PENDING').read_bytes()==b'preserved-review\n'
        proof=dict(passed=True,real_finalizer_invoked=True,archive_and_reassembly_SHA_verified=True,source_members=len(index['files']),unexecuted_not_scientific_pass=True,guard_preserved=True,models=0,physical_native=0)
    dump(O/'FINALIZER_QUALIFICATION.json',proof);print(json.dumps(proof))


if __name__=='__main__':main()
