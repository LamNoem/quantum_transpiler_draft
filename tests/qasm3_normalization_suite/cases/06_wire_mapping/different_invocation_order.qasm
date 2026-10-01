// TEST: 06_wire_mapping/different_invocation_order
// KIND: normalize
// PURPOSE: Reusing a custom rule must not reuse physical wire mappings.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate pair(t) a,b { rx(t) a; cy a,b; rz(t) b; }
qubit[3] q;
pair(pi/7) q[2],q[0];
pair(-pi/5) q[1],q[2];
