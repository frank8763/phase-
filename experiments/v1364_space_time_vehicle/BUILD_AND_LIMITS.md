# Build, artifacts and limits

All C++ uses existing original NumPy-equivalent rectangle geometry, original
spatial guide and pinned existing standalone Reeds–Shepp source through local
includes. No external library or network download added. Build each named
source independently with g++ -O3 -std=c++17 -shared -fPIC on CPU3/nice19:

|Source|runs/v1364_space_time_vehicle output|
|---|---|
|search.cpp|libtimed.so|
|interval_search.cpp|libinterval.so|
|interval_box.cpp|libinterval_box.so|
|interval_guided.cpp|libinterval_guided.so|
|interval_kinodynamic.cpp|libinterval_kinodynamic.so|
|qualification_seams.cpp|libqualification_seams.so|

Every kernel is a software prototype. Exact saved request03 refuses under
22000/1.5s; no physical program, launch script or model permission is supplied.
Individual search CPU timings are empirical; no realtime guarantee. Test
outputs report explicit cases and zero model/integration counts.

Preserve per-implementation original results and exact binary hashes. Do not
rerun qualify*.py into the same output namespace; create a separately registered
new diagnostic only when a specific source revision or unresolved check merits
it. No new candidate can reopen the expired17:00 physical window.

The interval versions merge by quantized pose/gear/speed/steering and reachable
time. This reduces duplicate work but has no proven continuous completeness.
Primitive steering changes remain nominal, not slew-qualified actual actuator
commands. Physical capture error/settling/stop and timing envelope unqualified.
No public path or clock manipulation may be substituted for those checks.
