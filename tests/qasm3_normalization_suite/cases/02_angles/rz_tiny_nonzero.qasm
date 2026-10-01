// TEST: 02_angles/rz_tiny_nonzero
// KIND: normalize
// PURPOSE: rz(1e-6): isolate sign, angle, zero/periodicity and phase mistakes.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rz(1e-6) q[0];
