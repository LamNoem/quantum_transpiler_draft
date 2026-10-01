// TEST: 06_wire_mapping/permuted_custom
// KIND: normalize
// PURPOSE: Preserve the ordered formal-to-actual mapping of a three-wire custom gate.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate asymmetric(t) a,b,c { ry(t) a; cx a,c; rz(t/2) b; cx c,b; }
qubit[4] q;
asymmetric(pi/7) q[3],q[0],q[2];
