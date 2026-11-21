"""Fixed finite evidence scopes, each using the original <=32MiB writer.

The once owner must reserve the sum of ALL scope caps before a model starts.
There is no compressed-size credit, cap renewal or on-demand global budget.
"""
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]
BLOCK=4096
NPZ_OVERHEAD_CAP=16384
JSON_CAP=16384
PER_SCOPE_MARGIN=256*1024


def raw_bytes(native):
    assert type(native)is int and native>=0
    return 216*(native+1)+168*native


def rounded(value):
    return ((value+BLOCK-1)//BLOCK)*BLOCK


def plan(boundaries):
    assert len(boundaries)==281 and sum(count for _,count in boundaries)==13600
    scopes={'root':4*1024**2}
    for phase in ('generation','audit'):
        scopes[phase]=4*1024**2
        scopes[phase+'/nominal']=rounded(raw_bytes(13600)+PER_SCOPE_MARGIN)
        for index,(offset,count)in enumerate(boundaries):
            assert type(offset)is type(count)is int and offset>=0 and count>0
            scopes[f'{phase}/b{index:03d}']=rounded(raw_bytes(2200)+raw_bytes(count+2200)+PER_SCOPE_MARGIN)
    assert all(16384<=value<=32*1024**2 for value in scopes.values())
    # The fixed 256KiB margin covers two NPZ headers (<=16KiB each),
    # four <=16KiB JSON files, six original metered opens/new paths,
    # the original 16KiB writer counter hold and per-file/block rounding.
    # A persistence attempt is made ONCE per branch, including on error.
    return dict(scopes=scopes,model_writer_bytes=sum(scopes.values()),
                max_scopes=len(scopes),original_writer_cap_bytes=32*1024**2,
                NPZ_overhead_cap_bytes=NPZ_OVERHEAD_CAP,JSON_cap_bytes=JSON_CAP,
                branch_persistence_attempts=1,compression_credit_bytes=0,
                raw_two_phase_array_bytes=970688016)


def branch_folder(phase_folder,name):
    if name in {'nominal','nominal_partial'}:
        return phase_folder/'nominal'
    prefix=name.split('_',1)[0]
    assert len(prefix)==4 and prefix[0]=='b'and prefix[1:].isdigit()
    assert 0<=int(prefix[1:])<281
    return phase_folder/prefix


class Storage:
    def __init__(self,root,*,source_identity,fixed_plan,purpose='NUMERIC_EVIDENCE'):
        self.root=Path(root).resolve()
        if purpose=='SOURCE_STORAGE_ONLY':
            assert self.root==R/'runs/v1552_complete_canonical_witness/source_target/model'
            import json
            parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
            assert parent['active_round']is None and not parent['models_now_authorized']
        else:
            assert purpose=='NUMERIC_EVIDENCE'
            assert self.root==R/'runs/v1552_complete_canonical_witness/model'
        assert self.root.is_dir()and not self.root.is_symlink()
        self.fixed_plan=fixed_plan
        self.identity=source_identity
        self.writers={}
        path=R/'experiments/v1436_pathlib_control_rename/writer_budget.py'
        spec=importlib.util.spec_from_file_location('v1552_original_per_scope_writer',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.original=module.WriterBudget

    def prepare_folder(self,folder):
        relative=Path(folder).relative_to(self.root)
        assert str(relative)in self.fixed_plan['scopes']
        folder.mkdir(parents=True,exist_ok=True)

    def reserve(self,path,pending_bytes):
        path=Path(path)
        assert path.is_absolute()and path.parent.resolve().is_relative_to(self.root)
        assert not path.is_symlink()and path.name not in {'','..'}
        relative=path.relative_to(self.root)
        parts=relative.parts
        if len(parts)==1:
            key='root';output=self.root
        elif len(parts)==2:
            key=parts[0];output=self.root/key
        else:
            assert len(parts)==3
            key='/'.join(parts[:2]);output=self.root/key
        assert key in self.fixed_plan['scopes'],'UNDECLARED_NONZERO_EVIDENCE_SCOPE'
        # Called while the original OutputBoundary's busy guard is held;
        # original counter/lock writes are covered by their original16KiB
        # hold and the fixed per-scope cap, not charged recursively.
        if key not in self.writers:
            output.mkdir(parents=True,exist_ok=True)
            self.writers[key]=self.original(output,role='PLANNER',
                maximum_bytes=self.fixed_plan['scopes'][key],source_identity=self.identity)
        return self.writers[key].reserve(path,pending_bytes)

    def accounting(self):
        values={key:writer._read()for key,writer in self.writers.items()}
        return dict(fixed_reserved_bytes=self.fixed_plan['model_writer_bytes'],
                    opened_scopes=len(values),maximum_scopes=self.fixed_plan['max_scopes'],
                    charged_bytes=sum(value['charged_bytes']for value in values.values()),
                    full_unopened_scopes_reserved=True,
                    per_scope_charged={key:value['charged_bytes']for key,value in values.items()})
