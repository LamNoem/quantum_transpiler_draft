// TEST: 02_angles/ry_near_two_pi
// KIND: normalize
// PURPOSE: Do not round a small nonzero residual in ry away.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
ry(2*pi + 1e-6) q[0];
