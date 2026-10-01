// TEST: 05_custom_recursive/multiple_instances
// KIND: normalize
// PURPOSE: Cached replacement DAGs must not retain parameters from another invocation.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate g(t) a { ry(t) a; rz(t/2) a; }
qubit[2] q;
g(pi/7) q[0];
g(pi/3) q[1];
g(-pi/5) q[0];
