"""Run unchanged real isolated entry and rejection qualification on new output."""
from pathlib import Path
R = Path(__file__).resolve().parents[2]
ORIGINAL = R/'experiments/v1086_ns_complete_repeat/qualify.py'
s = ORIGINAL.read_text()
old = "O = R/'runs/v1086_ns_complete_repeat'"
assert s.count(old) == 1
s = s.replace(old, "O = R/'runs/v1087_ns_repeat_after_shutdown'")
exec(compile(s, str(ORIGINAL), 'exec'), dict(__name__='__main__', __file__=str(ORIGINAL)))
