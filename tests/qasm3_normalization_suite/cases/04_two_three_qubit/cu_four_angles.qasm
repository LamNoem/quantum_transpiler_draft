// TEST: 04_two_three_qubit/cu_four_angles
// KIND: normalize
// PURPOSE: The fourth cu angle is a control-relative phase; do not omit it.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
cu(0.731,-0.413,1.127,0.293) q[0],q[1];
