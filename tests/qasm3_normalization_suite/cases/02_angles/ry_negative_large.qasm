// TEST: 02_angles/ry_negative_large
// KIND: normalize
// PURPOSE: ry(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
ry(-13*pi/9) q[0];
