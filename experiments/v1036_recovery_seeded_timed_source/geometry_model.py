"""Native-input geometry margin, with every original physical reserve retained."""
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.append(str(R/'experiments/v1022_full_route_planner'))
from full_route import ref,RHO
# The geometric primitive's sparse-sample and quadrature reserves apply to
# approximated geometry. Here complete original-controller native predictions
# replace that reference; retain every original actual-envelope/latency/20ms
# interpolation reserve. Physical clearance and tracking gates are unchanged.
REQUIRED=.155+ref._old.SPATIAL
