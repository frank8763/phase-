"""Zero-only renewal when Nav2 is silent; never replay a stale moving command."""
import math
SILENCE_S=.15

def due(phase,now,last_nominal_at):
 if phase!='RUNNING':return False
 if not math.isfinite(now):raise ValueError('NONFINITE_CLOCK')
 if last_nominal_at is None:return True
 if not math.isfinite(last_nominal_at)or now<last_nominal_at:raise ValueError('NONCAUSAL_COMMAND_CLOCK')
 return now-last_nominal_at>=SILENCE_S
