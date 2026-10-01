// TEST: 00_basics/empty_one_qubit
// KIND: normalize
// PURPOSE: An empty circuit is the identity; an empty DAG must not crash.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
