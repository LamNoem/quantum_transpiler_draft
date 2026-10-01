// TEST: 07_global_phase/z_vs_rz
// KIND: normalize
// PURPOSE: Z = exp(i*pi/2) RZ(pi). A missing phase is invisible to Operator.equiv.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
z q[0];
