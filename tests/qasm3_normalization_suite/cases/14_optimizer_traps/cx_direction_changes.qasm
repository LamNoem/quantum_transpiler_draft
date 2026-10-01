// TEST: 14_optimizer_traps/cx_direction_changes
// KIND: normalize
// PURPOSE: Opposite-direction CX gates do not cancel.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
cx q[0],q[1];
cx q[1],q[0];
