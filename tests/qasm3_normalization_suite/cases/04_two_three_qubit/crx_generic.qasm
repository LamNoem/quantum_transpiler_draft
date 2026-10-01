// TEST: 04_two_three_qubit/crx_generic
// KIND: normalize
// PURPOSE: Isolate crx; controlled phase and controlled rotation are different operations.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
crx(0.731) q[0],q[1];
