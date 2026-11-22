# Recover selected members with a checked continuation, no old helper retry

V1621 failed once at45s, leaving17035885bytes of part000. Its failure and bytes
remain. HEAD-only diagnosis returned200/33554432bytes in0.89s: asset exists,
the previous problem was an incomplete large transfer, not missing evidence.
One new bounded continuation uses direct Release URLs and Range for the exact
remaining bytes, requires206+Content-Range and complete original partSHA before
decompression. No retry of failed requests/parts.180s perrequest/1200sroot and
the V1620 absolute root, all15GiB limits. Copy the original partial to newscope,
keep original failure untouched. Single cached32MiB part, only two members kept.

Stop decompression after BOTH required members have exact original indexSHA.
Every part accessed before that is fully downloaded andSHAchecked, every
decoded member checked. This is SELECTED-MEMBER recovery, NOT a new fullarchive
readback; the original fullremote archive/index proof remains separately linked.
No oldmodels/worker/qualifier/physics/replay/sourcefixture or newtaskoutcomes.
