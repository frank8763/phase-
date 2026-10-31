"""Zero-navigation diagnostic of the inherited semantic state hash.
Execute current setup and stop before any candidate or environment step.
"""
from pathlib import Path
source=Path(__file__).with_name('run_static.py').read_text()
old='initial_hash=B.state_hash(env,shift,include_model=True)'
new="initial_hash,parts=B.state_hash(env,shift,include_model=True,components=True);dump(out/'initial_components.json',parts);raise RuntimeError('EXPECTED_ZERO_STEP_INITIAL_HASH_PROBE')"
assert source.count(old)==1
exec(compile(source.replace(old,new),str(Path(__file__).with_name('run_static.py')),'exec'))
