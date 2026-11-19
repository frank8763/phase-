# V1366 artifacts and verification entrypoints

All sources local, no physical imports in graph/forecast builders. C++ uses
original geometry and pinned Reeds–Shepp headers through frozen local includes.
Build on taskset CPU3/nice19 with g++ -O3 -std=c++17 -shared -fPIC:

|Source|runs/v1366_canonical_timed_lattice output|
|---|---|
|graph_search.cpp|libgraph.so|
|graph_polygon.cpp|libgraph_polygon.so|
|graph_adaptive.cpp|libgraph_adaptive.so|
|graph_horizon.cpp|libgraph_horizon.so|
|graph_cruise.cpp|libgraph_cruise.so|

Canonical initial construction and finite geometry search preprocesses are
explicit separate costs; do not call total end-to-end setup or real vehicle
navigation. Original kernel search1.5s/22000 bound remains, except an individual
boundary initialization may finish beyond that by arithmetic overhead, never a
realtime guarantee. Nominal curves have no actual actuator-response certificate.

Saved-source qualifications are run once per named namespace, no overwriting:
build_primitives.py,prepare_graph.py,build_polygons.py,run_saved.py,
check_graph.py,all_returns.py,timing_diagnosis.py,horizon_diagnosis.py,
cruise_edges.py. All artifacts including negative outcomes remain. Their
protocol amendments define conditional order, no unregistered sweep/seed.

Independent readbacks:audit_graph.py,audit_polygons.py,audit_cruise.py.
Real installed controller software:run_software.py,exactly2calls defined in
SOFTWARE_TASKS.json,commonINPUT_00 SHA,unchangedrpp/mppiparams. Completed
software/COMPLETION and INDEPENDENT_AUDIT,serverclosure and NoPhysical guard.
Never call stationary software playback physical navigation. No launch script,
new model permission or new physical hard window is present.

SOFTWARE_SOURCE_FREEZE in runs records exact pre-controller dependencies;
final SOURCE_FREEZE includes new diagnostic/closure sources and prior7865+
dependency closure. Final archive packs new source/outputs/report,fullmemberSHA
readback and32MiB transportparts;source/rawmembers retained until remote
downloaded SHA/member/restore verification. One new-round30spush+5sreadonly,
no repeats of previous round synchronization.
