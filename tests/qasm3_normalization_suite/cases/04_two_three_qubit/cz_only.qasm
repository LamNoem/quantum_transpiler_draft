// TEST: 04_two_three_qubit/cz_only
// KIND: normalize
// PURPOSE: Isolate cz; recursive replacement must terminate in the internal basis.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
cz q[0],q[1];
