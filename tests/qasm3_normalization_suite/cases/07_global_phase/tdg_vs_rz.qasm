// TEST: 07_global_phase/tdg_vs_rz
// KIND: normalize
// PURPOSE: TDG requires a negative global-phase correction in an exact RZ lowering.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
tdg q[0];
