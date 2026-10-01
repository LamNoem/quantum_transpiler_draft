// TEST: 05_custom_recursive/unused_formal_wire
// KIND: normalize
// PURPOSE: The first formal wire is unused but must remain in the substitution interface.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate touch_second(t) a,b { ry(t) b; }
qubit[3] q;
touch_second(pi/5) q[2],q[0];
