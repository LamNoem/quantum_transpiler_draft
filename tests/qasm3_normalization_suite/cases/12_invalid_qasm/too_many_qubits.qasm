// TEST: 12_invalid_qasm/too_many_qubits
// KIND: invalid_qasm
// PURPOSE: Wrong gate arity: H has one operand; comma-separated operands are not broadcasting.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0],q[1];
