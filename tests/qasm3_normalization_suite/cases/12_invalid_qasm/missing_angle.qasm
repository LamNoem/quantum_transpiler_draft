// TEST: 12_invalid_qasm/missing_angle
// KIND: invalid_qasm
// PURPOSE: Wrong parameter arity: RX needs an angle.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
rx q[0];
