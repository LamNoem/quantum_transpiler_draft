// TEST: 02_angles/p_four_pi
// KIND: normalize
// PURPOSE: p(4*pi): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
p(4*pi) q[0];
