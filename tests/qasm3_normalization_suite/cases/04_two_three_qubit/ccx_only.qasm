// TEST: 04_two_three_qubit/ccx_only
// KIND: normalize
// PURPOSE: Toffoli exposes multi-level decomposition and T/TDG handling.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
ccx q[0],q[1],q[2];
