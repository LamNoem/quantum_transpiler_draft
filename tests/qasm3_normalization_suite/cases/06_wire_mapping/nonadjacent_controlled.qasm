// TEST: 06_wire_mapping/nonadjacent_controlled
// KIND: normalize
// PURPOSE: Nonadjacent operands are valid at logical normalization; this is not a routing test.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[6] q;
h q[4];
cry(pi/7) q[4],q[1];
