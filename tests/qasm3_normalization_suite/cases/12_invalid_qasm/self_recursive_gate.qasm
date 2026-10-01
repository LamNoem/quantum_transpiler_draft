// TEST: 12_invalid_qasm/self_recursive_gate
// KIND: invalid_qasm
// PURPOSE: Recursive gate definitions are not legal OpenQASM; reject before Norm recursion.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
gate bad a { bad a; }
qubit[1] q;
bad q[0];
