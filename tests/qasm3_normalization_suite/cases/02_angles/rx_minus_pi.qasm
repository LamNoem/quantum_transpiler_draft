// TEST: 02_angles/rx_minus_pi
// KIND: normalize
// PURPOSE: rx(-pi): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(-pi) q[0];
