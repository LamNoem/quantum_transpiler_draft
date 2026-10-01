// TEST: 05_custom_recursive/empty_definition
// KIND: normalize
// PURPOSE: An empty gate definition means identity, not unsupported; erase the node without erasing wires.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate identity_gate a { }
qubit[1] q;
identity_gate q[0];
