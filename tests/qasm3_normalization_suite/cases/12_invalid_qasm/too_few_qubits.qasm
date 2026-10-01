// TEST: 12_invalid_qasm/too_few_qubits
// KIND: invalid_qasm
// PURPOSE: Wrong gate arity: CX requires two qubit operands.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cx q[0];
