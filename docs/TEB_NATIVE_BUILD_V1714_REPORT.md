# Original TEB isolated native build V1714

Original author9e55af4724310c34bcfa8cbb3b2783478c1a246a files unchanged, original recovered ROS/Ubuntu dependencies mounted read-only in a network-isolated namespace. Host fallback and exact package link/path mapping recorded. Build completion is not optimizer or navigation qualification.

```json
{
  "closed": true,
  "passed": false,
  "scope": "ORIGINAL_TEB_CPU4_LIBRARY_BUILD_ONLY",
  "first_error": {
    "error": "AssertionError(('configure_DEPENDENCY_OR_COMPILER_REFUSAL', 1))",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1714_teb_native_namespace/owner.py\", line 85, in main\n    run('configure',argv,180,view);result['configure_passed']=True;result['compile_calls']=1\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1714_teb_native_namespace/owner.py\", line 75, in run\n    assert child.returncode==0,(stage+'_DEPENDENCY_OR_COMPILER_REFUSAL',child.returncode)\nAssertionError: ('configure_DEPENDENCY_OR_COMPILER_REFUSAL', 1)\n"
  },
  "secondary_errors": [],
  "configure_calls": 1,
  "compile_calls": 0,
  "source_SHA_unchanged": true,
  "optimizer_constructors": 0,
  "optimizer_calls": 0,
  "optimizer_DLL_loads": 0,
  "other_toolchain_dynamic_load_count": null,
  "models": 0,
  "physical_native": 0,
  "replay_native": 0,
  "method_outcome": null,
  "allruns_bytes": 11484692480,
  "owner_and_child_gone": true,
  "review_original": true,
  "execution_idle": true,
  "all14079_shared_source_SHA_verified": true,
  "result_sha256": "d88815fc779c23fe5fbeb7de708e2f51f902f98140cfd8431be6713ed00347f4",
  "runtime_recovery_pending": true
}
```

Original RESULT and separate configure/compile consoles are authoritative; no old failed attempt was reopened.0optimizer/model/physical/replay.

Console-stage clarification: bwrap failed creating /phase-host/usr under the readonly root, before CMake exec. Original configure_calls=1 counts the wrapper command attempt; actual CMake/compiler calls0. WRAPPER_FAILURE_DIAGNOSIS.json is separate source-derived metadata; original machine RESULT remains unchanged.
