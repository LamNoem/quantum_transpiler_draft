// TEST: 14_optimizer_traps/two_x
// KIND: normalize
// PURPOSE: Two X gates may remain after normalization; cancellation is an optimization, not a normalization requirement.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
x q[0];
x q[0];
