// TEST: 12_invalid_qasm/measurement_in_gate
// KIND: invalid_qasm
// PURPOSE: A gate definition cannot contain measurement.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
gate bad a { measure a; }
qubit[1] q;
bad q[0];
