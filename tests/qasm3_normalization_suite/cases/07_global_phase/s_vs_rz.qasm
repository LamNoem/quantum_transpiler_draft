// TEST: 07_global_phase/s_vs_rz
// KIND: normalize
// PURPOSE: S = exp(i*pi/4) RZ(pi/2). Preserve or explicitly report the phase.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
s q[0];
