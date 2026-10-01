// TEST: 01_single_qubit/U_generic
// KIND: normalize
// PURPOSE: Built-in U is a key fallback endpoint: implement a terminating lowering rather than assuming definition exists.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
U(0.731,-0.413,1.127) q[0];
