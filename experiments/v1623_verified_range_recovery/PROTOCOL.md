# Positive-progress recovery after recorded transport refusals

V1621 original transfer timed out; V1622 completed part000 SHA but received
part001 body33525184 instead of33554432 (29248bytes short). Both failures stay.
New finite transport supports at most4 NONOVERLAPPING positive-progress ranges
perpart;206/Content-Range/length and final ORIGINAL partSHA are mandatory before
decompression. No request is retried after an exception, no fullpart replay to
repair a digest mismatch. Unverified originalpartials are copied unchanged;
their complete partSHA must pass before any bytes enter tar. Original failures
are not edited or resumed as campaigns. Required part000 must be reconstructed
again because the prior reader discarded its verified copy before its failure.

One1200s root and original V1620 root;single32MiB download cache plus original
failedpartials and retained<1MiB under15GiB/512MiBreserve. Stop after two exact
members, not a new fullarchive claim. Retain all failure/success originals.
No newmodels/native/physics/ROS/oldqualifier/benchmark outcomes. No further
transport-version loop if this bounded positive-progress reader refuses.
