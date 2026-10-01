// TEST: 06_wire_mapping/reversed_cx
// KIND: normalize
// PURPOSE: The control is q[2] and target is q[0]; never sort the qargs.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
x q[2];
cx q[2],q[0];
