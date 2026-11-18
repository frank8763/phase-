# V1331 public static information parity, preparation only

Zero models/physics/training. Build a conservative 5cm OccupancyGrid from the already public frozen V855 KNOWN_FIELD, identical information for RP-CCR/RPP/MPPI/future PRIEST. No new obstacles, actor ground truth, failed-state fitting, path/control change, ray-count change or threshold relaxation. Retain original 32-ray corrupted live scan layer in future candidates. The static map's dimensions include the originally declared [-5,5] boundary.

Every cell intersecting a known rectangle/circle or outside the arena is occupied; no safety padding baked into the map. Keep the original full footprint plus .15m padding in controllers. Cells are ordered bottom-to-top in OccupancyGrid; PGM top-to-bottom explicitly flipped. Validate all known entity boundaries and serialization reversibility. These are raster/input checks, not navigation, execution or safety certification.

Prepare common static-layer configurations for RPP and adapted MPPI. Existing historical scan-only pilots stay unchanged and cannot establish a fair comparative advantage. Actual installed Nav2 map receipt and obstruction rejection must pass software qualification before a separately frozen bounded physical batch. No physical launch or automatic dynamics/24 included here.
