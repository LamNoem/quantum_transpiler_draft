// TEST: 07_global_phase/phase_accumulation
// KIND: normalize
// PURPOSE: Accumulate all replacement phases rather than overwriting or dropping them.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
z q[0];
s q[1];
t q[0];
sdg q[0];
tdg q[1];
