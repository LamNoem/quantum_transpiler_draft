// TEST: 12_invalid_qasm/mismatched_broadcast
// KIND: invalid_qasm
// PURPOSE: Broadcast arrays must have equal lengths.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] a;
qubit[3] b;
cx a,b;
