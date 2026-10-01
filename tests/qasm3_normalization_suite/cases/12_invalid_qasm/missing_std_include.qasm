// TEST: 12_invalid_qasm/missing_std_include
// KIND: invalid_qasm
// PURPOSE: Without an include or definition, h is not a built-in; only U and gphase are built-in gates.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
qubit[1] q;
h q[0];
