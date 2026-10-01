// TEST: 09_directive_policy/barrier_after_measurements
// KIND: policy_probe
// PURPOSE: A trailing barrier is not quantum reuse; do not flag it as a gate after measurement.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[1] q;
h q[0];
c[0]=measure q[0];
barrier q[0];
