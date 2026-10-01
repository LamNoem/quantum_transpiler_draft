// TEST: 03_symbolic/nonalphabetical_parameters
// KIND: normalize
// PURPOSE: Never bind by guessed lexical or declaration order; bind Parameter objects.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta_2;
input float[64] theta_10;
input float[64] theta_1;
qubit[2] q;
ry(theta_10) q[0];
rx(theta_2) q[1];
cx q[1],q[0];
rz(theta_1-theta_10) q[1];
