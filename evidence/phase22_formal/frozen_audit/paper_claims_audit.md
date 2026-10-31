# Paper Claims Audit — Frozen

## Claims supported
- Phase22 improves collision-free task completion versus Phase21-v11 on the 300-pair held-out set.
- The gain is primarily associated with fewer hard wall-time/planning failures.
- G2A supports randomized unknown-obstacle generalization within the evaluated distribution.
- G3 shows positive pooled multi-scene direction, but not statistical significance.
- G4C shows Phase22 and frozen DWA have comparable collision-free task success on that 100-case paired set.
- Local ROS1/Noetic software graph and current-source catkin build were validated in isolation.

## Claims forbidden / unsupported
- Do NOT claim statistically significant collision reduction for Phase22.
- Do NOT claim Phase22 is overall superior to DWA.
- Do NOT claim real-time planner performance under the original predefined gate.
- Do NOT claim real-robot validation.
- Do NOT claim dynamic/moving-obstacle benchmark validation.
- Do NOT claim broad arbitrary unknown-obstacle generalization beyond tested distributions.
- Do NOT claim actual MK-mini vendor topic names, IP, serial, CAN or bring-up stack.
- Do NOT tune Final300 or G4C after opening those sets.

## Core wording
On a strictly held-out set of 300 paired randomized trials, the proposed method increased
collision-free task success from 55.00% to 71.33%, yielding a paired improvement of
16.33 percentage points. The collision rate changed from 19.00% to 21.67% without
evidence of a statistically significant reduction, while hard wall-time failures decreased
from 78 to 20.

Against the frozen Ackermann-compatible DWA baseline on 100 paired scenarios, Phase22
achieved 60.0% collision-free task success compared with 61.0% for DWA. This indicates
different failure-mode trade-offs rather than an overall efficacy advantage over DWA.
