// TEST: 03_symbolic/affine_expressions
// KIND: normalize
// PURPOSE: Preserve multiple parameter expressions and signs through substitutions.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
input float[64] phi;
qubit[1] q;
rx(2*theta + pi/7) q[0];
ry(-theta/3 + phi) q[0];
rz(theta-2*phi) q[0];
