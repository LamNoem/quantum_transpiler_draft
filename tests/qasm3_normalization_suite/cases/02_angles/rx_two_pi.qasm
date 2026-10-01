// TEST: 02_angles/rx_two_pi
// KIND: normalize
// PURPOSE: rx(2*pi): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.
// NOTE: Use exact operator comparison as well as equivalence up to global phase. 2*pi is not an exact identity for spin rotations.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(2*pi) q[0];
