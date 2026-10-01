// TEST: 10_language_features/ctrl_two_x
// KIND: feature_probe
// PURPOSE: Multiple controls and permuted qargs.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
ctrl(2) @ x q[2],q[0],q[1];
