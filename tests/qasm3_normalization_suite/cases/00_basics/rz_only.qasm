// TEST: 00_basics/rz_only
// KIND: normalize
// PURPOSE: A numerical internal RZ is already normalized.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
rz(pi/7) q[0];
