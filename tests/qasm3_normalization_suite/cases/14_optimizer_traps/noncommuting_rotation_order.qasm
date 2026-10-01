// TEST: 14_optimizer_traps/noncommuting_rotation_order
// KIND: normalize
// PURPOSE: Do not reverse operations while building a sub-DAG.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(pi/7) q[0];
ry(pi/5) q[0];
rz(pi/3) q[0];
