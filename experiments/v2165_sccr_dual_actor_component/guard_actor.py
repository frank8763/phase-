"""No-authority actor entry: must fail before Torch import."""
import sys
from actors import FrozenActor
try:FrozenActor(107)
except AssertionError as e:
 assert 'NOT_ADMITTED'in str(e)and 'torch'not in sys.modules
 print('ACTOR_GUARD_BEFORE_TORCH')
else:raise AssertionError('ACTOR_ADMISSION_BYPASS')
