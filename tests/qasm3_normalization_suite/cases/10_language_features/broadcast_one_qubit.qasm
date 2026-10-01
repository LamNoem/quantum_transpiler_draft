// TEST: 10_language_features/broadcast_one_qubit
// KIND: feature_probe
// PURPOSE: Broadcast a one-qubit operation to every member of a register.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
ry(pi/7) q;
