// TEST: 09_directive_policy/repeated_measurement
// KIND: policy_probe
// PURPOSE: Decide whether repeated final measurements of one qubit are supported or rejected.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

bit a;
bit b;
qubit[1] q;
h q[0];
a=measure q[0];
b=measure q[0];
