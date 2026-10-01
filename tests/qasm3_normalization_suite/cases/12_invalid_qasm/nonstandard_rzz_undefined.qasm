// TEST: 12_invalid_qasm/nonstandard_rzz_undefined
// KIND: invalid_qasm
// PURPOSE: RZZ is not automatically defined by the OpenQASM 3.0 standard library; provide a custom definition.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
rzz(pi/7) q[0],q[1];
