// TEST: 02_angles/rx_near_two_pi
// KIND: normalize
// PURPOSE: Do not round a small nonzero residual in rx away.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(2*pi + 1e-6) q[0];
