# Original TEB isolated native build V1724

Original author9e55af4724310c34bcfa8cbb3b2783478c1a246a files unchanged, original recovered ROS/Ubuntu dependencies mounted read-only in a network-isolated namespace. Host fallback and exact package link/path mapping recorded. Build completion is not optimizer or navigation qualification.

```json
{
  "closed": true,
  "passed": false,
  "scope": "ORIGINAL_TEB_CPU4_LIBRARY_BUILD_ONLY",
  "first_error": {
    "error": "AssertionError(('compile_DEPENDENCY_OR_COMPILER_REFUSAL', 2))",
    "traceback": "Traceback (most recent call last):\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1724_teb_focal_header_build/owner.py\", line 86, in main\n    run('compile',[binary,'--build',str(O/'build'),'--target','teb_local_planner','--parallel','1'],1800,view)\n  File \"/home/linghu/Documents/Codex/2026-10-31/new-chat/phase-/experiments/v1724_teb_focal_header_build/owner.py\", line 75, in run\n    assert child.returncode==0,(stage+'_DEPENDENCY_OR_COMPILER_REFUSAL',child.returncode)\nAssertionError: ('compile_DEPENDENCY_OR_COMPILER_REFUSAL', 2)\n"
  },
  "secondary_errors": [],
  "configure_calls": 1,
  "compile_calls": 1,
  "source_SHA_unchanged": true,
  "optimizer_constructors": 0,
  "optimizer_calls": 0,
  "optimizer_DLL_loads": 0,
  "other_toolchain_dynamic_load_count": null,
  "models": 0,
  "physical_native": 0,
  "replay_native": 0,
  "method_outcome": null,
  "allruns_bytes": 11542806528,
  "owner_and_child_gone": true,
  "review_original": true,
  "execution_idle": true,
  "all14079_shared_source_SHA_verified": true,
  "result_sha256": "946c87b4cdc91d350ae26c7c6a52e80c31ca21d44ec6b224d71c36d2e61eb7c9",
  "runtime_recovery_pending": true
}
```

Original RESULT and separate configure/compile consoles are authoritative; no old failed attempt was reopened.0optimizer/model/physical/replay.

All9 original author translation units compiled under exact original Focal C headers. GNU make then refused missing /usr/lib/x86_64-linux-gnu/libpython3.8.so before final link. LINK_BOUNDARY_DIAGNOSIS.json binds the9objectSHAs; no sourcepatch/optimizer/libraryload or methodresult.
