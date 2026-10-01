// TEST: 10_language_features/input_angle
// KIND: feature_probe
// PURPOSE: Probe input angle[64] support separately from input float[64].
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

input angle[64] theta;
qubit[1] q;
ry(theta) q[0];
