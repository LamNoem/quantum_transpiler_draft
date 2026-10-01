// TEST: 01_single_qubit/y_only
// KIND: normalize
// PURPOSE: Isolate the y lowering, including its global phase.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
y q[0];
