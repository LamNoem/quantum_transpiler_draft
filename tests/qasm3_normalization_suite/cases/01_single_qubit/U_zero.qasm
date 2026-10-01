// TEST: 01_single_qubit/U_zero
// KIND: normalize
// PURPOSE: Built-in U with zero angles is the identity.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
U(0,0,0) q[0];
