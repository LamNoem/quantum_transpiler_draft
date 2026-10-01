// TEST: 05_custom_recursive/one_level
// KIND: normalize
// PURPOSE: Replace a custom node with a body containing a non-internal RX.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate my_rx(a) t { rx(a) t; }
qubit[1] q;
my_rx(pi/7) q[0];
