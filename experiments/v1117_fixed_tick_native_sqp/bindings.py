"""Exact physically qualified V1114 mode/model; no physical factory imports."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
sys.path.insert(0,str(R/'experiments/rpccr_execution_core'))
from kernel import PARAMETERS,ref,REQUIRED
sys.path.insert(0,str(R/'experiments/v1108_parked_steering_handoff'))
sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
from coupled_model import Predictor,initial,GAIN
from coupled_control import Adapter
