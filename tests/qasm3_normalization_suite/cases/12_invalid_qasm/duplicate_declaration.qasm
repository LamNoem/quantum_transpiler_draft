// TEST: 12_invalid_qasm/duplicate_declaration
// KIND: invalid_qasm
// PURPOSE: Duplicate declaration in one scope.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
qubit[1] q;
