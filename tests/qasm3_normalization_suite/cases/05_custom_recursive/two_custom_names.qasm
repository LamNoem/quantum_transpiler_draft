// TEST: 05_custom_recursive/two_custom_names
// KIND: normalize
// PURPOSE: Different definitions with identical arity/parameters must not share a wrong cache entry.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate first(t) a { rx(t) a; }
gate second(t) a { ry(t) a; }
qubit[1] q;
first(0.71) q[0];
second(0.71) q[0];
