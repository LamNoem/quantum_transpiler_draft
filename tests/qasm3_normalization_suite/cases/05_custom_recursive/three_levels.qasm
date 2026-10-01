// TEST: 05_custom_recursive/three_levels
// KIND: normalize
// PURPOSE: A single sweep leaves middle/inner/custom or non-basis gates behind.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate inner(a) t { ry(a) t; s t; }
gate middle(a) c,t { inner(a/2) t; cz c,t; inner(-a) c; }
gate outer(a) c,t { middle(a) t,c; rx(a+pi/9) c; }
qubit[2] q;
outer(pi/7) q[0],q[1];
