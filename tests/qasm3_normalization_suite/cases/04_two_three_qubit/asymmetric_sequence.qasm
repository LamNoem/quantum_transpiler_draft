// TEST: 04_two_three_qubit/asymmetric_sequence
// KIND: normalize
// PURPOSE: Use non-symmetric states and controls so reversed wires cannot accidentally pass.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
h q[0];
ry(0.321) q[1];
crx(-0.713) q[1],q[0];
cy q[0],q[1];
rz(0.913) q[1];
