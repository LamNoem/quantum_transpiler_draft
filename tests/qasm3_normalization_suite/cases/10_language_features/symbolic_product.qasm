// TEST: 10_language_features/symbolic_product
// KIND: feature_probe
// PURPOSE: Probe non-affine symbolic expression support.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
input float[64] phi;
qubit[1] q;
ry(theta*phi) q[0];
