"""One disclosed output-scope continuation; scientific V856 source stays byte-identical."""
import hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v856_nav2_foundation';ROOT=R/'runs/v856_nav2_foundation';OUT=ROOT/'entry01'
sys.path.insert(0,str(C))
def install():
    import physics_backend
    original=physics_backend.initialize
    def initialize_with_experiment_output_scope(seed,out):
        context,native=original(seed,out)
        context['B'].OUT=ROOT
        assert Path(context['B'].OUT).resolve()==ROOT.resolve()
        # Same legacy audit hook is retained; writes to frozen source remain forbidden.
        for path in [R/'current/__write_probe_must_not_exist__',R/'runtime/__write_probe_must_not_exist__',R/'experiments/__write_probe_must_not_exist__']:
            try:context['B'].write_guard('open',(str(path),'w',__import__('os').O_WRONLY))
            except PermissionError:pass
            else:raise AssertionError('OUTPUT_SCOPE_GUARD_ESCAPED')
        return context,native
    physics_backend.initialize=initialize_with_experiment_output_scope
