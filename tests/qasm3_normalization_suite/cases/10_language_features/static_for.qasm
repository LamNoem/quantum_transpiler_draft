// TEST: 10_language_features/static_for
// KIND: policy_probe
// PURPOSE: A static loop is valid, but should be unrolled in a frontend before a flat DAG normalizer.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
for int i in [0:2] { ry(pi/7) q[i]; }
