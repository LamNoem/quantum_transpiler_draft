// TEST: 02_angles/rz_negative_large
// KIND: normalize
// PURPOSE: rz(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rz(-13*pi/9) q[0];
