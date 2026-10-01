// TEST: 02_angles/rz_large_angle
// KIND: normalize
// PURPOSE: rz(23*pi/7): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rz(23*pi/7) q[0];
