// TEST: 14_optimizer_traps/adjacent_inverse
// KIND: normalize
// PURPOSE: Correctness requires identity behavior, not a minimal output gate count.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(pi/7) q[0];
rx(-pi/7) q[0];
