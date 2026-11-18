"""Fixed saved prefix; thirteen final-section variables; no state reset."""
import sys,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'))
from timed_source import Solver as TimedSolver
import numpy as np
class Solver(TimedSolver):
 def __init__(self,x,path,gears,initial_guess=None):
  assert initial_guess is None,'NO_ADDITIONAL_SEED';self.registered=np.array(json.loads((C/'WARM_START.json').read_text())['selected_z']);super().__init__(x,path,gears,initial_guess=self.registered.copy());assert self.n==4 and self.registered.shape==(52,),'EXPECTED_REGISTERED_FOUR_SECTION_INPUT';self.fixed=np.r_[np.arange(36),np.arange(48,51)];self.free=np.r_[np.arange(36,48),51];self.lower[self.fixed]=self.registered[self.fixed];self.upper[self.fixed]=self.registered[self.fixed];self.reference_rows,self.reference_events=self.schedule(self.registered);self.prefix_native=self.reference_events[2][2];self.prefix_rows=self.reference_rows[:41]
 def simulate(self,z,reserved_final=False):
  z=np.asarray(z);assert np.array_equal(z[self.fixed],self.registered[self.fixed]),'FROZEN_PREFIX_VARIABLE_CHANGED';rows,events=self.schedule(z);assert rows[:41]==self.prefix_rows and events[2][2]==self.prefix_native,'FROZEN_PREFIX_SCHEDULE_CHANGED';return super().simulate(z,reserved_final)
