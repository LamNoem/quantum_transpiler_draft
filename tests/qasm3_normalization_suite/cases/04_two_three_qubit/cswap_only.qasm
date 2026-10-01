// TEST: 04_two_three_qubit/cswap_only
// KIND: normalize
// PURPOSE: Fredkin exposes nested three-qubit gate decompositions.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
cswap q[0],q[1],q[2];
