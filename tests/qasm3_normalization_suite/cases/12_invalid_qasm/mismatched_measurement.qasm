// TEST: 12_invalid_qasm/mismatched_measurement
// KIND: invalid_qasm
// PURPOSE: Measurement source/destination lengths differ.
// EXPECTED: Intentionally invalid source: reject in parsing or semantic validation.

OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[1] c;
c=measure q;
