// TEST: 06_wire_mapping/highest_wire
// KIND: normalize
// PURPOSE: One-qubit replacement must act on the original q[5], not local sub-DAG wire 0.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[6] q;
ry(pi/7) q[5];
