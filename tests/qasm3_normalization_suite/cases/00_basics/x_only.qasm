// TEST: 00_basics/x_only
// KIND: normalize
// PURPOSE: An internal X must remain usable without a definition fallback.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
x q[0];
