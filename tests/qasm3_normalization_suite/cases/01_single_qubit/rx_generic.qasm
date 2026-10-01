// TEST: 01_single_qubit/rx_generic
// KIND: normalize
// PURPOSE: Isolate rx at a non-special angle; avoid accidental Clifford-only correctness.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rx(0.731) q[0];
