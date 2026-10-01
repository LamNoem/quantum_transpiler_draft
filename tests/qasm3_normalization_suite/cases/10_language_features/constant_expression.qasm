// TEST: 10_language_features/constant_expression
// KIND: feature_probe
// PURPOSE: A compile-time const declaration may be an importer limitation, not a Norm defect.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

const float[64] theta = pi/7;
qubit[1] q;
rx(theta) q[0];
