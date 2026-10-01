// TEST: 02_angles/ry_generic_pi
// KIND: normalize
// PURPOSE: ry(pi/7): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
ry(pi/7) q[0];
