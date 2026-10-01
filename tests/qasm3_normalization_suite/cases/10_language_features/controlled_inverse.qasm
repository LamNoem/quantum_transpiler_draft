// TEST: 10_language_features/controlled_inverse
// KIND: feature_probe
// PURPOSE: Combine controlled and inverse semantics without losing phases.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
ctrl @ inv @ s q[0],q[1];
