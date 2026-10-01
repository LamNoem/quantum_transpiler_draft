// TEST: 09_directive_policy/discarded_measurement
// KIND: policy_probe
// PURPOSE: A measurement with no classical destination is valid QASM; decide whether the compiler accepts it.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
h q[0];
measure q[0];
