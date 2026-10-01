// TEST: 07_global_phase/cp_not_crz
// KIND: normalize
// PURPOSE: CP and CRZ must not share a naive lowering that discards the base-gate phase.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
h q[0];
h q[1];
cp(pi/3) q[0],q[1];
h q[0];
