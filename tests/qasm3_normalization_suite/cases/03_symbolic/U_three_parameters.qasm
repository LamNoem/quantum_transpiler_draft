// TEST: 03_symbolic/U_three_parameters
// KIND: normalize
// PURPOSE: An explicit U lowering must keep all three symbolic parameters in the correct order.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
input float[64] phi;
input float[64] lambda_;
qubit[1] q;
U(theta,phi,lambda_) q[0];
