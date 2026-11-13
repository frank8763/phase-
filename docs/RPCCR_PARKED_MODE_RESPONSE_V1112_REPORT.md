# V1112 parked-mode response: entry failure before integration

NOT_PASSED. The first canonical static vehicle initialized; actual integration0, own executed-control replay0, one replay data initialization. Neither fixed response test obtained physical motion. The second task was not initialized.

The entry guard incorrectly required the SHA from the NS actor-present dynamic source fixture, although this protocol explicitly registers an actor-absent static component. Saved setup differences are exactly `actor`, `dynamic`, and `model_sha256`; all other setup fields and the actual t0 body match. This is an assistant entry-contract error, not evidence that parked steering failed. The original saved-native audit also failed because no native trace exists at0 steps; that original error is preserved.

The true static t0 metadata and compiled SHA are retained in records/nav2_v1112_20261113/STATIC_T0_SOURCE_FIXTURE.json for a future pre-model scope check. No compiled-array equivalence between the static and dynamic models is claimed.

Both software schema audits and16 rejection cases passed before freeze; those synthetic tests did not cover the static-versus-dynamic fixture mismatch. Future qualification must reject inconsistent task/fixture scope before physical construction.

Original source freeze, failure result and90-minute root window are retained without changes. No model restart, scientific patch, full route, three-route or24 trial was launched after closure. REVIEW_PENDING restored byte-for-byte and Phase execution lock idle.

```json
{
  "closed": true,
  "passed": false,
  "version": "v1112",
  "scope": "two original static t0 parked-steering components only",
  "attempted": [
    "negative_to_positive"
  ],
  "unexecuted": [
    "positive_to_negative"
  ],
  "counts": {
    "vehicle_initializations": 1,
    "new_actual_native": 0,
    "own_replay_native": 0,
    "replay_state_initializations": 1,
    "private_mujoco_native": 0,
    "training_updates": 0
  },
  "error": {
    "error": "AssertionError('FIRST_RESPONSE_SAFETY_OR_EVIDENCE_FAILURE')",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1112_parked_mode_response/campaign.py\", line 45, in main\n    assert row['passed'],'FIRST_RESPONSE_SAFETY_OR_EVIDENCE_FAILURE'\nAssertionError: FIRST_RESPONSE_SAFETY_OR_EVIDENCE_FAILURE\n"
  },
  "source_unchanged": true,
  "guard_original": true,
  "whole_route_passed": false,
  "new24_executed": false,
  "closed_unix": 1794567603.7207534
}
```
