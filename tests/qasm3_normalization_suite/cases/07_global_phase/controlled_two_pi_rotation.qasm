// TEST: 07_global_phase/controlled_two_pi_rotation
// KIND: normalize
// PURPOSE: A controlled 2*pi rotation is not the identity; the control acquires a relative minus sign.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
h q[0];
crx(2*pi) q[0],q[1];
h q[0];
