// TEST: 03_symbolic/rz_input
// KIND: normalize
// PURPOSE: Normalize rz before binding theta; no float(theta) conversion.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

input float[64] theta;
qubit[1] q;
rz(theta) q[0];
