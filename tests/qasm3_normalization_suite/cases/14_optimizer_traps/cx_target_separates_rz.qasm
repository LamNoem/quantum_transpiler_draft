// TEST: 14_optimizer_traps/cx_target_separates_rz
// KIND: normalize
// PURPOSE: RZ on the CX target cannot generally be moved through CX.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
rz(pi/7) q[1];
cx q[0],q[1];
rz(pi/5) q[1];
