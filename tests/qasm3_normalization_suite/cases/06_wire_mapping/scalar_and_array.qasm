// TEST: 06_wire_mapping/scalar_and_array
// KIND: normalize
// PURPOSE: Preserve a scalar ancilla and a separate array register.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit anc;
qubit[2] q;
rx(pi/7) anc;
cy q[1],anc;
rz(-pi/5) q[0];
