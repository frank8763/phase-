# Fix the demonstrated stdin transport mismatch, software only

V2073 failed once before a normal native command or optimizer event with
UNBOUND_WRITABLE_DESCRIPTOR at subprocess.Popen(stdin=PIPE) inside the original
OutputBoundary. Its200actual/200replay/errorstop, independent prefix audit,
runtime remote barrier and first error remain immutable. It is a technical
integration failure, not SVG performance refusal or a formal slot.

The exact original Python boundary and real subprocess constructor reproduced
the same assertion without a model. Ranked falsifiable predictions:
1. Anonymous writable stdin is rejected by io.open: a quota-controlled regular
   input file opened read-only for the child will pass under the same boundary.
2. An output path escape is responsible: moving that same input outside the
   allowed output must still fail, while an in-scope path passes.
3. A descriptor lifetime/race is responsible: a real child consuming a full
   bounded frame and echoing its hash must match exactly with the file held open
   until child exit. No timing relaxation is introduced.

New helper writes one <=1MiB exact JSON frame with the original scoped writer,
then passes a read-only regular input stream to the child. It never exempts raw
descriptors, pipes or arbitrary paths from the old boundary. One CPU5 software
fixture with <=256KiB temporary input and <=128KiB report, within preparation
16MiB. Test original failure, byte-exact delivery, outside-path rejection,
oversize rejection, repeated input refusal and unchanged raw-descriptor guard.
No model/optimizer/physics/replay/audit/formal claim or physical retry. A later
source qualification and separate resource/admission contract are required
before this helper can enter a vehicle experiment.
