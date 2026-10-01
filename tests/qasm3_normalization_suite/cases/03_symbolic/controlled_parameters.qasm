// TEST: 03_symbolic/controlled_parameters
// KIND: normalize
// PURPOSE: Parameter expressions must survive multi-qubit decompositions.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
input float[64] phi;
qubit[2] q;
h q[0];
cp(theta) q[0],q[1];
cry(phi) q[1],q[0];
crz(theta-phi) q[0],q[1];
