// TEST: 09_directive_policy/delay
// KIND: policy_probe
// PURPOSE: Timing information is outside unitary gate normalization; preserve elsewhere or reject explicitly.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
h q[0];
delay[10ns] q[0];
x q[0];
