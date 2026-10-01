// TEST: 04_two_three_qubit/cry_generic
// KIND: normalize
// PURPOSE: Isolate cry; controlled phase and controlled rotation are different operations.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
cry(0.731) q[0],q[1];
