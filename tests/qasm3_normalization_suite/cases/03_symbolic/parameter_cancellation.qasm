// TEST: 03_symbolic/parameter_cancellation
// KIND: normalize
// PURPOSE: A cancelled parameter may disappear; do not demand parameter-set equality after valid optimization.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
qubit[1] q;
rz(theta) q[0];
rz(-theta) q[0];
