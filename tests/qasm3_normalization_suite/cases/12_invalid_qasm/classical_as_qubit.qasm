// TEST: 12_invalid_qasm/classical_as_qubit
// KIND: invalid_qasm
// PURPOSE: Type error: a classical bit is not a gate operand.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
bit[1] c;
h c[0];
