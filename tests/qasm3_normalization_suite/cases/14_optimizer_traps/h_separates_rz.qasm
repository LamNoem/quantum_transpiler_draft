// TEST: 14_optimizer_traps/h_separates_rz
// KIND: normalize
// PURPOSE: Never merge RZ rotations through a noncommuting H.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rz(pi/7) q[0];
h q[0];
rz(pi/5) q[0];
