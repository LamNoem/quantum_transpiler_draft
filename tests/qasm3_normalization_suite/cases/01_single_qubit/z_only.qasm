// TEST: 01_single_qubit/z_only
// KIND: normalize
// PURPOSE: Isolate the z lowering, including its global phase.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
z q[0];
